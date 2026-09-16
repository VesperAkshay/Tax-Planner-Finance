"""
Upload and Parsing Status API Endpoints (Tasks 8.1 & 8.2).

Provides:
- Statement upload endpoint (CSV and PDF bank statements) wired to Phase 2 parsing
  and Phase 3 ML categorization.
- Salary slip upload endpoint wired to Phase 2 Docling salary extractor.
- Parsing status endpoint returning parse_status, parse_confidence, and needs_review per upload.
"""

import hashlib
import logging
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.categorization.categorizer import TransactionCategorizer
from app.database import get_db_session
from app.models.account import Account
from app.models.category import Category
from app.models.salary_slip import SalarySlip
from app.models.statement_upload import StatementUpload
from app.models.transaction import Transaction
from app.models.user import User
from app.parsing.balance_reconciler import reconcile_statement_balance
from app.parsing.csv_parser import CSVBankParser
from app.parsing.pdf_parser import DoclingPDFParser
from app.parsing.salary_slip_parser import DoclingSalarySlipParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Document Upload"])

_categorizer_instance: Optional[TransactionCategorizer] = None


def get_categorizer() -> TransactionCategorizer:
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = TransactionCategorizer()
    return _categorizer_instance


# ==============================================================================
# Response Schemas
# ==============================================================================


class StatementUploadResponse(BaseModel):
    upload_id: int
    account_id: int
    file_name: str
    file_type: str
    parse_status: str
    parse_confidence: float
    balance_reconciled: bool
    needs_review: bool
    transactions_count: int
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None


class ParsingStatusResponse(BaseModel):
    upload_id: int
    file_name: str
    file_type: str
    parse_status: str
    parse_confidence: Optional[float]
    balance_reconciled: bool
    needs_review: bool
    transactions_count: int
    created_at: str


class SalarySlipUploadResponse(BaseModel):
    id: int
    file_name: str
    month: int
    year: int
    financial_year: str
    basic: float
    hra: float
    gross_pay: float
    employee_pf: float
    net_pay: float
    extraction_confidence: Optional[float]
    is_gross_valid: bool
    needs_review: bool


# ==============================================================================
# Endpoints
# ==============================================================================


@router.post("/statement", response_model=StatementUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_bank_statement(
    file: UploadFile = File(...),
    account_id: Optional[int] = Form(None),
    bank_format: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> StatementUploadResponse:
    """
    Uploads and parses a bank statement (CSV or PDF).
    Runs Phase 2 document parsing, Phase 3 ML categorization, balance reconciliation,
    and stores parsed records in Neon DB (Task 8.1).
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    # 1. Resolve or verify user's account
    if account_id:
        acc = session.get(Account, account_id)
        if not acc or acc.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account with ID {account_id} not found for this user.",
            )
    else:
        # Fetch or create user's default account
        acc = session.exec(select(Account).where(Account.user_id == current_user.id)).first()
        if not acc:
            acc = Account(
                user_id=current_user.id,
                account_name="Primary Savings",
                bank_name="Default Bank",
            )
            session.add(acc)
            session.commit()
            session.refresh(acc)

    # 2. Save uploaded content to temporary storage for parser ingestion
    file_name = file.filename or "statement"
    suffix = Path(file_name).suffix.lower()
    file_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # 3. Parse via Phase 2 pipeline
        if suffix == ".csv":
            csv_parser = CSVBankParser()
            parse_res = csv_parser.parse(tmp_path, bank_id=bank_format)
            file_type = "csv"
        elif suffix in [".pdf", ".png", ".jpg", ".jpeg"]:
            pdf_parser = DoclingPDFParser()
            parse_res = pdf_parser.parse(tmp_path)
            file_type = "pdf_text"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{suffix}'. Allowed: CSV, PDF.",
            )

        # 4. Check balance reconciliation
        parse_res = reconcile_statement_balance(parse_res)
        balance_reconciled = bool(parse_res.balance_reconciled)

        # 5. Insert StatementUpload record
        confidence_val = float(parse_res.parse_confidence) if parse_res.parse_confidence is not None else 1.0
        upload_rec = StatementUpload(
            user_id=current_user.id,
            account_id=acc.id,
            file_name=file_name,
            file_path=str(tmp_path),
            file_type=file_type,
            file_hash=file_hash,
            parse_status="completed" if confidence_val >= 0.85 else "needs_review",
            parse_confidence=round(confidence_val, 4),
            balance_reconciled=balance_reconciled,
            opening_balance=parse_res.opening_balance,
            closing_balance=parse_res.closing_balance,
            statement_start_date=parse_res.statement_start_date,
            statement_end_date=parse_res.statement_end_date,
            needs_review=(confidence_val < 0.85 or not balance_reconciled),
            raw_metadata={"file_name": parse_res.file_name, "raw_row_count": len(parse_res.rows)},
        )
        session.add(upload_rec)
        session.commit()
        session.refresh(upload_rec)

        # 6. Load Category cache for ID resolution
        all_categories = {c.name.lower(): c.id for c in session.exec(select(Category)).all()}
        categorizer = get_categorizer()

        # 7. Batch Categorize across Tier 1 (Patterns) -> Tier 2 (XGBoost) -> Tier 3 (LLM)
        descriptions = [r.description for r in parse_res.rows]
        cat_results = categorizer.categorize_batch(
            descriptions,
            use_llm_fallback=True,
            user_id=current_user.id,
        )

        db_txns: List[Transaction] = []
        for row, cat_res in zip(parse_res.rows, cat_results):
            assigned_cat_name = cat_res.category
            cat_id = all_categories.get(assigned_cat_name.lower())
            clean_desc = cat_res.clean_merchant or getattr(row, "cleaned_description", None) or row.description

            txn = Transaction(
                account_id=acc.id,
                upload_id=upload_rec.id,
                date=row.date,
                description=row.description,
                cleaned_description=clean_desc,
                amount=row.amount,
                transaction_type=row.transaction_type,
                balance=row.balance,
                reference_number=row.reference_number,
                category_id=cat_id,
                parse_confidence=row.parse_confidence,
                parse_status="parsed" if (row.parse_confidence and row.parse_confidence >= 0.85) else "flagged",
                balance_reconciled=balance_reconciled,
                category_confidence=cat_res.confidence,
                is_self_transfer=getattr(row, "is_self_transfer", False),
                needs_review=(row.needs_review or cat_res.needs_review),
            )
            db_txns.append(txn)
            session.add(txn)

        session.commit()

        return StatementUploadResponse(
            upload_id=upload_rec.id,
            account_id=acc.id,
            file_name=file_name,
            file_type=file_type,
            parse_status=upload_rec.parse_status,
            parse_confidence=upload_rec.parse_confidence or 1.0,
            balance_reconciled=balance_reconciled,
            needs_review=upload_rec.needs_review,
            transactions_count=len(db_txns),
            opening_balance=upload_rec.opening_balance,
            closing_balance=upload_rec.closing_balance,
        )

    finally:
        # Clean up temporary upload file
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


@router.post("/salary-slip", response_model=SalarySlipUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_salary_slip(
    file: UploadFile = File(...),
    month: Optional[int] = Form(None),
    year: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SalarySlipUploadResponse:
    """
    Uploads and extracts structured compensation data from a salary slip (Task 8.1).
    Extracts Basic, HRA, Gross Pay, Net Pay, and Employee PF into the salary_slips table.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    file_name = file.filename or "salary_slip.pdf"
    suffix = Path(file_name).suffix.lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        parser = DoclingSalarySlipParser()
        slip_res = parser.parse(tmp_path)

        slip_month = month or slip_res.month or 4
        slip_year = year or slip_res.year or 2025

        slip_rec = SalarySlip(
            user_id=current_user.id,
            file_name=file_name,
            file_path=str(tmp_path),
            month=slip_month,
            year=slip_year,
            financial_year=slip_res.financial_year or "2025-2026",
            basic=slip_res.basic,
            hra=slip_res.hra,
            lta=slip_res.lta,
            special_allowance=slip_res.special_allowance,
            other_allowances=slip_res.other_allowances,
            gross_pay=slip_res.gross_pay,
            employee_pf=slip_res.employee_pf,
            employer_pf=slip_res.employer_pf,
            professional_tax=slip_res.professional_tax,
            tds=slip_res.tds,
            other_deductions=slip_res.other_deductions,
            total_deductions=slip_res.total_deductions,
            net_pay=slip_res.net_pay,
            extraction_confidence=slip_res.extraction_confidence,
            is_gross_valid=slip_res.is_gross_valid,
            needs_review=slip_res.needs_review,
        )
        session.add(slip_rec)
        session.commit()
        session.refresh(slip_rec)

        return SalarySlipUploadResponse(
            id=slip_rec.id,
            file_name=slip_rec.file_name,
            month=slip_rec.month,
            year=slip_rec.year,
            financial_year=slip_rec.financial_year,
            basic=slip_rec.basic,
            hra=slip_rec.hra,
            gross_pay=slip_rec.gross_pay,
            employee_pf=slip_rec.employee_pf,
            net_pay=slip_rec.net_pay,
            extraction_confidence=slip_rec.extraction_confidence,
            is_gross_valid=slip_rec.is_gross_valid,
            needs_review=slip_rec.needs_review,
        )

    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


@router.get("/status/{upload_id}", response_model=ParsingStatusResponse)
def get_upload_parsing_status(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ParsingStatusResponse:
    """
    Task 8.2: Returns parsing status, confidence, review flag, and transaction count.
    Strictly scoped to the authenticated user.
    """
    stmt = (
        select(StatementUpload)
        .where(StatementUpload.id == upload_id)
        .where(StatementUpload.user_id == current_user.id)
    )
    upload = session.exec(stmt).first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement upload with ID {upload_id} not found for this user.",
        )

    txn_count = len(session.exec(select(Transaction).where(Transaction.upload_id == upload.id)).all())

    return ParsingStatusResponse(
        upload_id=upload.id,
        file_name=upload.file_name,
        file_type=upload.file_type,
        parse_status=upload.parse_status,
        parse_confidence=upload.parse_confidence,
        balance_reconciled=upload.balance_reconciled,
        needs_review=upload.needs_review,
        transactions_count=txn_count,
        created_at=upload.created_at.isoformat(),
    )

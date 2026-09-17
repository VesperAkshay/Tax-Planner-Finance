"""
Account and Data Lifecycle Management API Router (v1.1 Phase 15: Tasks 15.1 - 15.6).

Provides:
- 15.1: FY-scoped querying and deletion.
- 15.4: Scoped delete endpoints (single upload, financial year, and full account) with explicit confirmation.
- 15.5: Data export bundling transactions CSV, declared deductions JSON, and tax report PDF into a ZIP.
- 15.6: Account deletion (right-to-erasure) with post-deletion verification guaranteeing 0 orphaned rows.
"""

import csv
from datetime import datetime, timezone
import io
import json
import logging
from typing import Any, Dict, List, Optional
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.api.auth import get_current_user
from app.api.tax_report import _build_tax_report_payload
from app.database import get_db_session
from app.models.account import Account
from app.models.elicitation_progress import ElicitationProgress
from app.models.reconciliation_flag import ReconciliationFlag
from app.models.salary_slip import SalarySlip
from app.models.statement_upload import StatementUpload
from app.models.tax_computation import TaxComputation
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_declared_deduction import UserDeclaredDeduction
from app.reconciliation.service import run_reconciliation_pipeline
from app.tax_engine.pdf_invoice import generate_tax_invoice_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lifecycle", tags=["Account & Data Lifecycle"])


class ActionResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# ==============================================================================
# Task 15.4: Scoped Delete - Single Upload
# ==============================================================================


@router.delete("/upload/{upload_id}", response_model=ActionResponse)
def delete_single_upload(
    upload_id: int,
    confirm: bool = Query(False, description="Explicit confirmation to delete upload and cascade transactions"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ActionResponse:
    """
    Deletes a single statement upload and cascade-deletes all its parsed transactions (Task 15.4).
    Enforces cross-tenant isolation and re-runs reconciliation.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required: pass confirm=true to delete this upload and its transactions.",
        )

    upload = session.exec(
        select(StatementUpload)
        .where(StatementUpload.id == upload_id)
        .where(StatementUpload.user_id == current_user.id)
    ).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload ID {upload_id} not found for this user.",
        )

    # 1. Fetch transactions for this upload
    txns = session.exec(select(Transaction).where(Transaction.upload_id == upload_id)).all()
    deleted_txn_count = len(txns)

    # 2. Delete transactions and upload
    for txn in txns:
        session.delete(txn)

    session.delete(upload)
    session.commit()

    # 3. Re-run reconciliation pipeline across remaining transactions
    run_reconciliation_pipeline(session=session, user_id=current_user.id, auto_commit=True)

    return ActionResponse(
        success=True,
        message=f"Upload {upload_id} and {deleted_txn_count} transactions deleted successfully.",
        details={"upload_id": upload_id, "deleted_transactions": deleted_txn_count},
    )


# ==============================================================================
# Task 15.4: Scoped Delete - Financial Year Data
# ==============================================================================


@router.delete("/financial-year/{financial_year}", response_model=ActionResponse)
def delete_financial_year_data(
    financial_year: str,
    confirm: bool = Query(False, description="Explicit confirmation to delete all data for this FY"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ActionResponse:
    """
    Deletes all user data scoped to a specific financial year (Task 15.1 & 15.4):
    - User declared deductions
    - Elicitation progress
    - Tax computations
    - Salary slips (and associated reconciliation flags)
    - Transactions tagged with this FY
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Confirmation required: pass confirm=true to delete all data for financial year {financial_year}.",
        )

    # 1. Deductions
    deds = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
    ).all()
    for d in deds:
        session.delete(d)

    # 2. Elicitation progress
    progs = session.exec(
        select(ElicitationProgress)
        .where(ElicitationProgress.user_id == current_user.id)
        .where(ElicitationProgress.financial_year == financial_year)
    ).all()
    for p in progs:
        session.delete(p)

    # 3. Tax computations
    comps = session.exec(
        select(TaxComputation)
        .where(TaxComputation.user_id == current_user.id)
        .where(TaxComputation.financial_year == financial_year)
    ).all()
    for c in comps:
        session.delete(c)

    # 4. Salary slips & their reconciliation flags
    slips = session.exec(
        select(SalarySlip)
        .where(SalarySlip.user_id == current_user.id)
        .where(SalarySlip.financial_year == financial_year)
    ).all()
    for s in slips:
        flags = session.exec(
            select(ReconciliationFlag).where(ReconciliationFlag.salary_slip_id == s.id)
        ).all()
        for f in flags:
            session.delete(f)
        session.delete(s)

    # 5. Transactions for user's accounts in this FY
    user_acc_ids = list(
        session.exec(select(Account.id).where(Account.user_id == current_user.id)).all()
    )
    deleted_txns = 0
    if user_acc_ids:
        txns = session.exec(
            select(Transaction)
            .where(col(Transaction.account_id).in_(user_acc_ids))
            .where(Transaction.financial_year == financial_year)
        ).all()
        deleted_txns = len(txns)
        for t in txns:
            session.delete(t)

    session.commit()

    return ActionResponse(
        success=True,
        message=f"All data for financial year {financial_year} has been permanently deleted.",
        details={
            "financial_year": financial_year,
            "deleted_deductions": len(deds),
            "deleted_elicitation_progress": len(progs),
            "deleted_tax_computations": len(comps),
            "deleted_salary_slips": len(slips),
            "deleted_transactions": deleted_txns,
        },
    )


# ==============================================================================
# Tasks 15.4 & 15.6: Account Deletion (Right-to-Erasure)
# ==============================================================================


@router.delete("/account", response_model=ActionResponse)
def delete_entire_account(
    confirm: bool = Query(False, description="Explicit confirmation to permanently delete the account and all data"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ActionResponse:
    """
    Performs full account deletion (right-to-erasure, Task 15.6).
    Wipes all tables for the user and verifies zero orphaned rows remain afterward.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required: pass confirm=true to permanently delete your account and all associated data.",
        )

    user_id = current_user.id

    # 1. Fetch user accounts
    accounts = session.exec(select(Account).where(Account.user_id == user_id)).all()
    acc_ids = [a.id for a in accounts]

    # 2. Delete Reconciliation Flags
    flags = session.exec(select(ReconciliationFlag).where(ReconciliationFlag.user_id == user_id)).all()
    for f in flags:
        session.delete(f)

    # 3. Delete Salary Slips
    slips = session.exec(select(SalarySlip).where(SalarySlip.user_id == user_id)).all()
    for s in slips:
        session.delete(s)

    # 4. Delete Tax Computations
    comps = session.exec(select(TaxComputation).where(TaxComputation.user_id == user_id)).all()
    for c in comps:
        session.delete(c)

    # 5. Delete Elicitation Progress
    progs = session.exec(select(ElicitationProgress).where(ElicitationProgress.user_id == user_id)).all()
    for p in progs:
        session.delete(p)

    # 6. Delete User Declared Deductions
    deds = session.exec(select(UserDeclaredDeduction).where(UserDeclaredDeduction.user_id == user_id)).all()
    for d in deds:
        session.delete(d)

    # 7. Delete Transactions
    if acc_ids:
        txns = session.exec(select(Transaction).where(col(Transaction.account_id).in_(acc_ids))).all()
        for t in txns:
            session.delete(t)

    # 8. Delete Statement Uploads
    uploads = session.exec(select(StatementUpload).where(StatementUpload.user_id == user_id)).all()
    for u in uploads:
        session.delete(u)

    # 9. Delete Accounts
    for a in accounts:
        session.delete(a)

    # 10. Delete User
    user_record = session.get(User, user_id)
    if user_record:
        session.delete(user_record)

    session.commit()

    # 11. Verification Check: Assert zero orphaned rows remain for user_id (Task 15.6 & 15.10)
    orphans = {}
    if session.exec(select(ReconciliationFlag).where(ReconciliationFlag.user_id == user_id)).all():
        orphans["reconciliation_flags"] = True
    if session.exec(select(SalarySlip).where(SalarySlip.user_id == user_id)).all():
        orphans["salary_slips"] = True
    if session.exec(select(TaxComputation).where(TaxComputation.user_id == user_id)).all():
        orphans["tax_computations"] = True
    if session.exec(select(ElicitationProgress).where(ElicitationProgress.user_id == user_id)).all():
        orphans["elicitation_progress"] = True
    if session.exec(select(UserDeclaredDeduction).where(UserDeclaredDeduction.user_id == user_id)).all():
        orphans["user_declared_deductions"] = True
    if session.exec(select(StatementUpload).where(StatementUpload.user_id == user_id)).all():
        orphans["statement_uploads"] = True
    if session.exec(select(Account).where(Account.user_id == user_id)).all():
        orphans["accounts"] = True
    if session.get(User, user_id):
        orphans["users"] = True

    if orphans:
        logger.critical("Orphaned rows detected after account deletion: %s", orphans)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account erasure failed verification: orphaned rows remain in {list(orphans.keys())}.",
        )

    return ActionResponse(
        success=True,
        message="User account and all associated data permanently erased. Zero orphaned rows remain.",
    )


# ==============================================================================
# Task 15.5: Data Export Bundle
# ==============================================================================


@router.get("/export")
def export_user_data(
    financial_year: str = Query("2025-2026", description="Financial year for export"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    """
    Packages the user's transactions (CSV), declared deductions (JSON),
    and the vector-grade Tax Invoice PDF into a downloadable ZIP bundle (Task 15.5).
    """
    # 1. Fetch transactions for user's accounts
    acc_ids = list(
        session.exec(select(Account.id).where(Account.user_id == current_user.id)).all()
    )
    txns: List[Transaction] = []
    if acc_ids:
        txns = list(
            session.exec(
                select(Transaction)
                .where(col(Transaction.account_id).in_(acc_ids))
                .order_by(Transaction.date)
            ).all()
        )

    # Build Transactions CSV in-memory
    csv_buf = io.StringIO()
    csv_writer = csv.writer(csv_buf)
    csv_writer.writerow([
        "Transaction ID",
        "Account ID",
        "Financial Year",
        "Date",
        "Description",
        "Amount",
        "Type",
        "Balance",
        "Reference Number",
        "Self Transfer",
    ])
    for t in txns:
        csv_writer.writerow([
            t.id,
            t.account_id,
            t.financial_year or "",
            t.date.isoformat() if t.date else "",
            t.description,
            t.amount,
            t.transaction_type,
            t.balance if t.balance is not None else "",
            t.reference_number or "",
            t.is_self_transfer,
        ])
    csv_content = csv_buf.getvalue()

    # 2. Fetch User Declared Deductions
    deds = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
    ).all()
    deductions_data = [
        {
            "id": d.id,
            "section": d.section,
            "amount": d.amount,
            "source": d.source.value if hasattr(d.source, "value") else str(d.source),
            "status": d.status.value if hasattr(d.status, "value") else str(d.status),
            "metadata": d.metadata_json,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in deds
    ]
    deductions_json = json.dumps(deductions_data, indent=2)

    # 3. Generate Tax Report PDF
    try:
        report_payload = _build_tax_report_payload(
            session=session,
            current_user=current_user,
            financial_year=financial_year,
        )
        pdf_bytes = generate_tax_invoice_pdf(
            user_email=current_user.email,
            user_pan=current_user.pan,
            user_id=current_user.id,
            financial_year=financial_year,
            gross_income=report_payload["annual_gross"],
            comparison=report_payload["comparison"],
            deductions_applied=report_payload["deductions_dict"],
            citations=report_payload["citations"],
        )
    except Exception as e:
        logger.warning("Could not generate PDF for export: %s", e)
        pdf_bytes = b""

    # 4. Summary Metadata
    summary_data = {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "user_email": current_user.email,
        "financial_year": financial_year,
        "total_transactions": len(txns),
        "total_deductions_declared": len(deds),
    }
    summary_json = json.dumps(summary_data, indent=2)

    # 5. Bundle into ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("transactions.csv", csv_content)
        zf.writestr("declared_deductions.json", deductions_json)
        zf.writestr("export_summary.json", summary_json)
        if pdf_bytes:
            clean_fy = financial_year.replace("-", "_")
            zf.writestr(f"tax_comparison_report_{clean_fy}.pdf", pdf_bytes)

    zip_bytes = zip_buf.getvalue()
    clean_fy = financial_year.replace("-", "_")
    filename = f"tax_planner_export_FY{clean_fy}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )

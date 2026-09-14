"""
Tax Comparison Report API Endpoint (Task 8.6).

Combines:
- Phase 5 pure function tax regime comparison (Section 115BAC vs Old Regime).
- User-declared deductions pulled from Neon DB.
- Phase 6 statutory RAG citations attached with official URLs.
- Persistence into the tax_computations table.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.common import get_utc_now
from app.models.salary_slip import SalarySlip
from app.models.tax_computation import TaxComputation
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_declared_deduction import UserDeclaredDeduction
from app.rag.retriever import retrieve_tax_rules
from app.tax_engine.comparator import compare_regimes
from app.tax_engine.rules_loader import load_tax_rules

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax", tags=["Tax Reports"])


class TaxComparisonReportResponse(BaseModel):
    user_id: int
    financial_year: str
    gross_income: float
    is_salaried: bool
    recommended_regime: str
    tax_savings: float
    breakeven_deductions: float
    old_regime: Dict[str, Any]
    new_regime: Dict[str, Any]
    deductions_applied: Dict[str, Any]
    citations: List[Dict[str, Any]]
    summary: str


@router.get("/comparison-report", response_model=TaxComparisonReportResponse)
def get_tax_comparison_report(
    gross_income: Optional[float] = Query(None, ge=0.0, description="Override gross annual income"),
    is_salaried: bool = Query(True, description="Whether salaried standard deduction applies"),
    financial_year: str = Query("2025-2026", description="Financial year"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TaxComparisonReportResponse:
    """
    Generates and persists the final Tax Comparison Report for the authenticated user (Task 8.6).
    Applies zero LLM tax arithmetic; pure deterministic Python calculations strictly loaded from rules.
    """
    # 1. Determine gross income from user parameter, salary slips, or credit transactions
    annual_gross = gross_income
    if annual_gross is None:
        slips = session.exec(
            select(SalarySlip)
            .where(SalarySlip.user_id == current_user.id)
            .where(SalarySlip.financial_year == financial_year)
            .order_by(SalarySlip.month.desc())
        ).all()

        if slips:
            if len(slips) >= 12:
                annual_gross = sum(s.gross_pay for s in slips[:12])
            else:
                annual_gross = slips[0].gross_pay * 12.0
        else:
            # Fallback to credit transactions
            credit_txns = session.exec(select(Transaction).where(Transaction.transaction_type == "credit")).all()
            user_txns = [t for t in credit_txns if t.account and t.account.user_id == current_user.id]
            annual_gross = sum(t.amount for t in user_txns) if user_txns else 0.0

    annual_gross = max(0.0, float(annual_gross))

    # 2. Fetch user-declared deductions from database (Task 7.3 persistence)
    ded_records = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
    ).all()

    deductions_dict: Dict[str, Any] = {}
    for rec in ded_records:
        sec = rec.section.upper()
        if sec == "80C":
            deductions_dict["section_80c"] = rec.amount
        elif sec == "80D":
            deductions_dict["section_80d"] = rec.metadata_json if rec.metadata_json else rec.amount
        elif sec in ["80CCD(1B)", "80CCD_1B", "NPS"]:
            deductions_dict["section_80ccd_1b"] = rec.amount
        elif sec == "80G":
            deductions_dict["section_80g"] = rec.amount
        elif sec in ["24B", "SECTION 24(B)", "24(B)"]:
            deductions_dict["section_24b"] = rec.amount
        elif sec == "HRA":
            deductions_dict["hra"] = rec.metadata_json if rec.metadata_json else {"rent_paid": rec.amount}

    # 3. Compute pure comparison via Phase 5 tax engine
    rules = load_tax_rules()
    comparison = compare_regimes(
        gross_income=annual_gross,
        deductions=deductions_dict,
        rules=rules,
        is_salaried=is_salaried,
    )

    old_res = comparison["old"]
    new_res = comparison["new"]

    # 4. Attach grounded RAG citations from Phase 6
    citations: List[Dict[str, Any]] = []
    # Standard deduction citation
    sd_chunk = retrieve_tax_rules("standard deduction salaried employees", top_k=1, section_filter="Standard Deduction")
    if sd_chunk:
        citations.append({
            "section": "Standard Deduction",
            "title": sd_chunk[0]["title"],
            "source_url": sd_chunk[0]["source_url"],
        })

    # Citations for claimed deductions
    if deductions_dict.get("section_80c", 0) > 0:
        c_chunk = retrieve_tax_rules("80C deduction limit", top_k=1, section_filter="80C")
        if c_chunk:
            citations.append({"section": "80C", "title": c_chunk[0]["title"], "source_url": c_chunk[0]["source_url"]})

    if deductions_dict.get("section_80d"):
        d_chunk = retrieve_tax_rules("80D medical insurance", top_k=1, section_filter="80D")
        if d_chunk:
            citations.append({"section": "80D", "title": d_chunk[0]["title"], "source_url": d_chunk[0]["source_url"]})

    if deductions_dict.get("section_80ccd_1b", 0) > 0:
        nps_chunk = retrieve_tax_rules("80CCD 1B NPS deduction", top_k=1, section_filter="80CCD(1B)")
        if nps_chunk:
            citations.append({"section": "80CCD(1B)", "title": nps_chunk[0]["title"], "source_url": nps_chunk[0]["source_url"]})

    if deductions_dict.get("section_80g", 0) > 0:
        g_chunk = retrieve_tax_rules("80G donations limit", top_k=1, section_filter="80G")
        if g_chunk:
            citations.append({"section": "80G", "title": g_chunk[0]["title"], "source_url": g_chunk[0]["source_url"]})

    if deductions_dict.get("section_24b", 0) > 0:
        b24_chunk = retrieve_tax_rules("24b home loan interest", top_k=1, section_filter="Section 24(b)")
        if b24_chunk:
            citations.append({"section": "Section 24(b)", "title": b24_chunk[0]["title"], "source_url": b24_chunk[0]["source_url"]})

    if deductions_dict.get("hra"):
        hra_chunk = retrieve_tax_rules("HRA exemption calculation", top_k=1, section_filter="Section 10(13A)")
        if hra_chunk:
            citations.append({"section": "Section 10(13A)", "title": hra_chunk[0]["title"], "source_url": hra_chunk[0]["source_url"]})

    # Section 87A rebate citation
    r87_chunk = retrieve_tax_rules("Section 87A rebate marginal relief", top_k=1, section_filter="Section 87A")
    if r87_chunk:
        citations.append({"section": "Section 87A", "title": r87_chunk[0]["title"], "source_url": r87_chunk[0]["source_url"]})

    # 5. Persist or update TaxComputation row in Neon DB
    computation_rec = session.exec(
        select(TaxComputation)
        .where(TaxComputation.user_id == current_user.id)
        .where(TaxComputation.financial_year == financial_year)
    ).first()

    if computation_rec:
        computation_rec.gross_income = annual_gross
        computation_rec.old_regime_taxable_income = old_res["taxable_income"]
        computation_rec.old_regime_tax = old_res["tax_before_rebate"]
        computation_rec.old_regime_cess = old_res["cess"]
        computation_rec.old_regime_total_liability = old_res["total_tax"]
        computation_rec.new_regime_taxable_income = new_res["taxable_income"]
        computation_rec.new_regime_tax = new_res["tax_before_rebate"]
        computation_rec.new_regime_cess = new_res["cess"]
        computation_rec.new_regime_total_liability = new_res["total_tax"]
        computation_rec.recommended_regime = comparison["recommended"]
        computation_rec.tax_savings = comparison["savings"]
        computation_rec.deductions_applied = deductions_dict
        computation_rec.computation_breakdown = comparison
        computation_rec.updated_at = get_utc_now()
        session.add(computation_rec)
    else:
        computation_rec = TaxComputation(
            user_id=current_user.id,
            financial_year=financial_year,
            gross_income=annual_gross,
            old_regime_taxable_income=old_res["taxable_income"],
            old_regime_tax=old_res["tax_before_rebate"],
            old_regime_cess=old_res["cess"],
            old_regime_total_liability=old_res["total_tax"],
            new_regime_taxable_income=new_res["taxable_income"],
            new_regime_tax=new_res["tax_before_rebate"],
            new_regime_cess=new_res["cess"],
            new_regime_total_liability=new_res["total_tax"],
            recommended_regime=comparison["recommended"],
            tax_savings=comparison["savings"],
            deductions_applied=deductions_dict,
            computation_breakdown=comparison,
        )
        session.add(computation_rec)

    session.commit()

    return TaxComparisonReportResponse(
        user_id=current_user.id,
        financial_year=financial_year,
        gross_income=annual_gross,
        is_salaried=is_salaried,
        recommended_regime=comparison["recommended"],
        tax_savings=comparison["savings"],
        breakeven_deductions=comparison["breakeven_deductions"],
        old_regime=old_res,
        new_regime=new_res,
        deductions_applied=deductions_dict,
        citations=citations,
        summary=comparison["summary"],
    )

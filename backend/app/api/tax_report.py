"""
Tax Comparison Report API Endpoint (Task 8.6 + Phase 17 Upgrade).

Combines:
- Phase 5 pure function tax regime comparison (Section 115BAC vs Old Regime).
- User-declared deductions pulled from Neon DB.
- Phase 6 statutory RAG citations attached with official URLs.
- Persistence into the tax_computations table.
- Phase 17 Real-World Coverage:
  - 17.1: Savings interest detection (80TTA / 80TTB) feeding income and deduction separately.
  - 17.2: Capital gains & ITR-2 advisory warning.
  - 17.3: Arrears detection & Section 89 relief warning.
  - 17.4: AIS & Form 26AS reconciliation checklist.
  - 17.5: Filing deadline countdown indicator.
  - 17.6: Year-over-year comparison across multi-year data.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.account import Account
from app.models.common import get_utc_now
from app.models.elicitation_progress import ElicitationProgress
from app.models.salary_slip import SalarySlip
from app.models.tax_computation import TaxComputation
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_declared_deduction import UserDeclaredDeduction
from app.rag.retriever import retrieve_tax_rules
from app.tax_engine.comparator import compare_regimes
from app.tax_engine.pdf_invoice import generate_tax_invoice_pdf
from app.tax_engine.real_world_detectors import (
    compute_filing_deadline_countdown,
    compute_year_over_year_comparison_data,
    detect_capital_gains_activity,
    detect_salary_arrears,
    detect_savings_interest,
    get_ais_26as_checklist,
)
from app.tax_engine.rules_loader import load_tax_rules

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax", tags=["Tax Reports"])


class TaxComparisonReportResponse(BaseModel):
    user_id: int
    financial_year: str
    gross_income: float
    salary_income: Optional[float] = None
    savings_interest_income: Optional[float] = None
    is_salaried: bool
    recommended_regime: str
    tax_savings: float
    breakeven_deductions: float
    old_regime: Dict[str, Any]
    new_regime: Dict[str, Any]
    deductions_applied: Dict[str, Any]
    citations: List[Dict[str, Any]]
    summary: str
    catalog_viewed: bool = False
    is_final: bool = False
    report_status: str = "draft"
    real_world_flags: Optional[Dict[str, Any]] = None
    ais_26as_checklist: Optional[Dict[str, Any]] = None
    filing_deadline: Optional[Dict[str, Any]] = None


def _build_tax_report_payload(
    session: Session,
    current_user: User,
    gross_income: Optional[float] = None,
    is_salaried: bool = True,
    financial_year: str = "2025-2026",
) -> Dict[str, Any]:
    """
    Shared deterministic payload generator for both JSON report and PDF invoice export.
    """
    # Fetch user transactions for this financial year across accounts
    user_all_txns_query = (
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(Account.user_id == current_user.id)
    )
    user_txns_all = list(session.exec(user_all_txns_query).all())
    user_fy_txns = [t for t in user_txns_all if t.financial_year == financial_year]
    active_txns = user_fy_txns if user_fy_txns else user_txns_all

    # Run Real-World Detectors (Phase 17)
    savings_interest_res = detect_savings_interest(active_txns, is_senior_citizen=False)
    cg_res = detect_capital_gains_activity(active_txns)
    arrears_res = detect_salary_arrears(active_txns)
    ais_checklist = get_ais_26as_checklist()
    deadline_info = compute_filing_deadline_countdown(financial_year=financial_year)

    # 1. Determine gross salary / baseline income
    annual_gross = gross_income
    slips = []
    if annual_gross is None:
        slips = list(session.exec(
            select(SalarySlip)
            .where(SalarySlip.user_id == current_user.id)
            .where(SalarySlip.financial_year == financial_year)
            .order_by(SalarySlip.month.desc())
        ).all())

        if slips:
            if len(slips) >= 12:
                annual_gross = sum(s.gross_pay for s in slips[:12])
            else:
                annual_gross = slips[0].gross_pay * 12.0
        else:
            # Fallback to credit transactions
            credit_user_txns = [t for t in active_txns if t.transaction_type == "credit"]
            annual_gross = sum(t.amount for t in credit_user_txns) if credit_user_txns else 0.0

    salary_income = max(0.0, float(annual_gross))
    savings_interest_income = savings_interest_res["total_interest"]

    # Ingest savings interest into gross total income (Task 17.1)
    # If annual_gross came from salary slips or manual override, add savings interest to gross income.
    # If annual_gross was fallback from credit transactions, savings interest was already part of the sum.
    if gross_income is not None or slips:
        total_gross_income = round(salary_income + savings_interest_income, 2)
    else:
        total_gross_income = round(salary_income, 2)
        salary_income = round(max(0.0, total_gross_income - savings_interest_income), 2)

    # 2. Fetch user-declared deductions from database (Task 7.3 persistence)
    ded_records = list(session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
    ).all())

    sec_key_map = {
        "80C": "section_80c",
        "80CCD(1B)": "section_80ccd_1b",
        "80CCD_1B": "section_80ccd_1b",
        "NPS": "section_80ccd_1b",
        "80CCD(2)": "section_80ccd_2",
        "80CCD_2": "section_80ccd_2",
        "80D": "section_80d",
        "80D (PARENTS)": "section_80d_parents",
        "10(13A)": "hra",
        "HRA": "hra",
        "80GG": "section_80gg",
        "24B": "section_24b",
        "24(B)": "section_24b",
        "SECTION 24(B)": "section_24b",
        "80EEA": "section_80eea",
        "80E": "section_80e",
        "80G": "section_80g",
        "80GGC": "section_80ggc",
        "80TTA": "section_80tta",
        "80TTB": "section_80ttb",
        "80DD": "section_80dd",
        "80DDB": "section_80ddb",
        "80U": "section_80u",
        "10(5)": "section_10_5",
        "LTA": "section_10_5",
    }
    deductions_dict: Dict[str, Any] = {}
    for rec in ded_records:
        sec = (rec.section or "").strip().upper()
        mapped_key = sec_key_map.get(sec, sec.lower().replace("-", "_").replace(" ", "_"))
        if mapped_key == "hra":
            deductions_dict["hra"] = rec.metadata_json if rec.metadata_json else {"rent_paid": rec.amount}
        elif mapped_key == "section_80d":
            deductions_dict["section_80d"] = rec.metadata_json if rec.metadata_json else rec.amount
        else:
            deductions_dict[mapped_key] = rec.metadata_json if rec.metadata_json else rec.amount

    # Feed detected savings interest deduction into deductions_dict (Task 17.1)
    if savings_interest_income > 0:
        sec_key = "section_80ttb" if savings_interest_res["eligible_section"] == "80TTB" else "section_80tta"
        if deductions_dict.get(sec_key, 0.0) <= 0.0:
            deductions_dict[sec_key] = savings_interest_res["allowable_deduction"]

    # 3. Check completion checkpoint: has user viewed full deduction catalog? (Task 14.7)
    checkpoint_rec = session.exec(
        select(ElicitationProgress)
        .where(ElicitationProgress.user_id == current_user.id)
        .where(ElicitationProgress.financial_year == financial_year)
        .where(ElicitationProgress.section_code == "__CATALOG_VIEWED__")
    ).first()
    catalog_viewed = checkpoint_rec is not None
    is_final = catalog_viewed
    report_status = "final" if is_final else "draft"

    # 4. Compute pure comparison via Phase 5 tax engine
    rules = load_tax_rules()
    comparison = compare_regimes(
        gross_income=total_gross_income,
        deductions=deductions_dict,
        rules=rules,
        is_salaried=is_salaried,
    )

    old_res = comparison["old"]
    new_res = comparison["new"]

    # 5. Attach grounded RAG citations from Phase 6
    citations: List[Dict[str, Any]] = []
    sd_chunk = retrieve_tax_rules("standard deduction salaried employees", top_k=1, section_filter="Standard Deduction")
    if sd_chunk:
        citations.append({
            "section": "Standard Deduction",
            "title": sd_chunk[0]["title"],
            "source_url": sd_chunk[0]["source_url"],
        })

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

    if deductions_dict.get("section_80tta", 0) > 0:
        tta_chunk = retrieve_tax_rules("80TTA savings interest deduction", top_k=1, section_filter="80TTA")
        if tta_chunk:
            citations.append({"section": "80TTA", "title": tta_chunk[0]["title"], "source_url": tta_chunk[0]["source_url"]})

    if deductions_dict.get("section_80ttb", 0) > 0:
        ttb_chunk = retrieve_tax_rules("80TTB senior citizen interest deduction", top_k=1, section_filter="80TTB")
        if ttb_chunk:
            citations.append({"section": "80TTB", "title": ttb_chunk[0]["title"], "source_url": ttb_chunk[0]["source_url"]})

    r87_chunk = retrieve_tax_rules("Section 87A rebate marginal relief", top_k=1, section_filter="Section 87A")
    if r87_chunk:
        citations.append({"section": "Section 87A", "title": r87_chunk[0]["title"], "source_url": r87_chunk[0]["source_url"]})

    # 6. Persist or update TaxComputation row in Neon DB
    computation_rec = session.exec(
        select(TaxComputation)
        .where(TaxComputation.user_id == current_user.id)
        .where(TaxComputation.financial_year == financial_year)
    ).first()

    if computation_rec:
        computation_rec.gross_income = total_gross_income
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
            gross_income=total_gross_income,
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

    real_world_flags = {
        "savings_interest": savings_interest_res,
        "capital_gains": cg_res,
        "salary_arrears": arrears_res,
    }

    return {
        "annual_gross": total_gross_income,
        "salary_income": salary_income,
        "savings_interest_income": savings_interest_income,
        "is_salaried": is_salaried,
        "financial_year": financial_year,
        "comparison": comparison,
        "old_res": old_res,
        "new_res": new_res,
        "deductions_dict": deductions_dict,
        "citations": citations,
        "catalog_viewed": catalog_viewed,
        "is_final": is_final,
        "report_status": report_status,
        "real_world_flags": real_world_flags,
        "ais_26as_checklist": ais_checklist,
        "filing_deadline": deadline_info,
    }


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
    Includes Phase 17 Real-World coverage: savings interest, capital gains, arrears, AIS checklist, deadline.
    """
    payload = _build_tax_report_payload(
        session=session,
        current_user=current_user,
        gross_income=gross_income,
        is_salaried=is_salaried,
        financial_year=financial_year,
    )
    comparison = payload["comparison"]

    return TaxComparisonReportResponse(
        user_id=current_user.id,
        financial_year=payload["financial_year"],
        gross_income=payload["annual_gross"],
        salary_income=payload.get("salary_income"),
        savings_interest_income=payload.get("savings_interest_income"),
        is_salaried=payload["is_salaried"],
        recommended_regime=comparison["recommended"],
        tax_savings=comparison["savings"],
        breakeven_deductions=comparison["breakeven_deductions"],
        old_regime=payload["old_res"],
        new_regime=payload["new_res"],
        deductions_applied=payload["deductions_dict"],
        citations=payload["citations"],
        summary=comparison["summary"],
        catalog_viewed=payload["catalog_viewed"],
        is_final=payload["is_final"],
        report_status=payload["report_status"],
        real_world_flags=payload.get("real_world_flags"),
        ais_26as_checklist=payload.get("ais_26as_checklist"),
        filing_deadline=payload.get("filing_deadline"),
    )


@router.get("/comparison-report/pdf")
def get_tax_comparison_report_pdf(
    gross_income: Optional[float] = Query(None, ge=0.0, description="Override gross annual income"),
    is_salaried: bool = Query(True, description="Whether salaried standard deduction applies"),
    financial_year: str = Query("2025-2026", description="Financial year"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    """
    Generates a high-resolution, vector-grade Neo-Brutalist PDF Invoice Memo
    comparing Old vs New Tax Regimes side-by-side for direct download (Phase 12).
    Includes Phase 17 filing deadline, statutory advisories, and AIS checklist.
    """
    payload = _build_tax_report_payload(
        session=session,
        current_user=current_user,
        gross_income=gross_income,
        is_salaried=is_salaried,
        financial_year=financial_year,
    )

    pdf_bytes = generate_tax_invoice_pdf(
        user_email=current_user.email,
        user_pan=current_user.pan,
        user_id=current_user.id,
        financial_year=payload["financial_year"],
        gross_income=payload["annual_gross"],
        comparison=payload["comparison"],
        deductions_applied=payload["deductions_dict"],
        citations=payload["citations"],
        real_world_flags=payload.get("real_world_flags"),
        ais_26as_checklist=payload.get("ais_26as_checklist"),
        filing_deadline=payload.get("filing_deadline"),
    )

    clean_fy = financial_year.replace("-", "_")
    filename = f"Mr_Planner_Tax_Invoice_FY{clean_fy}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/year-over-year")
def get_tax_year_over_year(
    current_fy: str = Query("2025-2026", description="Current financial year"),
    prior_fy: Optional[str] = Query(None, description="Prior financial year to compare"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Compares current financial year's tax computation against prior financial year (Task 17.6).
    Highlights income, deduction, regime, and tax liability differentials.
    """
    if not prior_fy:
        try:
            parts = current_fy.split("-")
            curr_start = int(parts[0])
            prior_fy = f"{curr_start - 1}-{curr_start}"
        except Exception:
            prior_fy = "2024-2025"

    curr_payload = _build_tax_report_payload(session=session, current_user=current_user, financial_year=current_fy)

    # Check if prior FY computation exists or if there is prior year data
    prior_rec = session.exec(
        select(TaxComputation)
        .where(TaxComputation.user_id == current_user.id)
        .where(TaxComputation.financial_year == prior_fy)
    ).first()

    prior_data = None
    if prior_rec:
        prior_data = {
            "financial_year": prior_rec.financial_year,
            "gross_income": prior_rec.gross_income,
            "old_regime_total_liability": prior_rec.old_regime_total_liability,
            "new_regime_total_liability": prior_rec.new_regime_total_liability,
            "recommended_regime": prior_rec.recommended_regime,
            "tax_savings": prior_rec.tax_savings,
        }
    else:
        # Check if transactions or salary slips exist for prior FY
        prior_txns = list(session.exec(
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(Account.user_id == current_user.id)
            .where(Transaction.financial_year == prior_fy)
        ).all())
        prior_slips = list(session.exec(
            select(SalarySlip)
            .where(SalarySlip.user_id == current_user.id)
            .where(SalarySlip.financial_year == prior_fy)
        ).all())
        if prior_txns or prior_slips:
            prior_payload = _build_tax_report_payload(session=session, current_user=current_user, financial_year=prior_fy)
            prior_data = {
                "financial_year": prior_fy,
                "gross_income": prior_payload["annual_gross"],
                "old_regime_total_liability": prior_payload["old_res"]["total_tax"],
                "new_regime_total_liability": prior_payload["new_res"]["total_tax"],
                "recommended_regime": prior_payload["comparison"]["recommended"],
                "tax_savings": prior_payload["comparison"]["savings"],
            }

    curr_summary = {
        "financial_year": current_fy,
        "gross_income": curr_payload["annual_gross"],
        "old_regime_total_liability": curr_payload["old_res"]["total_tax"],
        "new_regime_total_liability": curr_payload["new_res"]["total_tax"],
        "recommended_regime": curr_payload["comparison"]["recommended"],
        "tax_savings": curr_payload["comparison"]["savings"],
    }

    return compute_year_over_year_comparison_data(curr_summary, prior_data)

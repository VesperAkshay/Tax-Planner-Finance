"""
Real-World Tax & Income Coverage Detectors (v1.1 Phase 17).

Pure deterministic Python functions to detect commonly-missed, high-impact filing issues:
- 17.1: Savings account interest detection (80TTA / 80TTB) feeding income and deduction separately.
- 17.2: Capital gains & ITR form eligibility indicator (flags MF redemptions / stock broker credits; never computes capital gains).
- 17.3: Arrears detection & Section 89 relief warning (flags anomalous one-time salary spikes).
- 17.4: AIS & Form 26AS reconciliation checklist generator.
- 17.5: Filing deadline countdown awareness indicator (July 31 of Assessment Year).
- 17.6: Year-over-year tax & liability comparison across multi-year data.
"""

from datetime import date, datetime
import re
import statistics
from typing import Any, Dict, List, Optional, Union

# Regex patterns for savings bank interest identification (Task 17.1)
INTEREST_PATTERNS = re.compile(
    r"(?:int(?:erest)?\.?\s*(?:pd|paid|cr|credited|earned|appl|applied)?|"
    r"sb\s*int|savings\s*int|credit\s*interest|cr\s*int|qtrly\s*int|"
    r"quarterly\s*interest|capitali[zs]ed\s*int|int\.capitalized)",
    re.IGNORECASE,
)

# Term deposit / FD interest indicators to differentiate pure savings interest if non-senior
TERM_DEPOSIT_PATTERNS = re.compile(
    r"(?:term\s*deposit|tdr|fixed\s*deposit|fd\s*int|fd\s*interest|reinvestment)",
    re.IGNORECASE,
)

# Regex patterns for mutual fund redemptions and broker payouts (Task 17.2)
CAPITAL_GAINS_PATTERNS = re.compile(
    r"\b(?:cams|kfintech|karvy|zerodha|groww|upstox|angel\s*one|icici\s*securities|"
    r"i-sec|motilal|sharekhan|uti\s*mf|hdfc\s*mf|sbi\s*mf|nippon|axis\s*mf|mirae|"
    r"mutual\s*fund\s*redemption|mf\s*redemption|brokerage\s*payout|5paisa|"
    r"paytm\s*money|dhan|geojit|kotak\s*securities|clearing\s*corp|iccl|nscl|ncl)\b",
    re.IGNORECASE,
)

# Regex patterns for salary credits (Task 17.3)
SALARY_PATTERNS = re.compile(
    r"\b(?:salary|sal\s*cr|sal\s*credit|payroll|monthly\s*sal|monthly\s*pay|salary\s*for)\b",
    re.IGNORECASE,
)

ARREARS_KEYWORDS = re.compile(r"\b(?:arrear|arrears|pay\s*revision|retrospective)\b", re.IGNORECASE)


def _get_txn_attr(txn: Any, attr: str, default: Any = None) -> Any:
    """Helper to safely read attributes from SQLModel instances or dictionaries."""
    if isinstance(txn, dict):
        return txn.get(attr, default)
    return getattr(txn, attr, default)


def detect_savings_interest(
    transactions: List[Any],
    is_senior_citizen: bool = False,
) -> Dict[str, Any]:
    """
    Task 17.1: Scans transactions for recurring savings account interest credits.
    - Computes total reportable interest income.
    - Determines eligible deduction under Section 80TTA (up to ₹10,000 for regular individuals)
      or Section 80TTB (up to ₹50,000 for senior citizens 60+).
    - Returns structured information to feed both taxable income and eligible deduction separately.
    """
    matched_txns: List[Dict[str, Any]] = []
    total_interest = 0.0

    for txn in transactions:
        txn_type = str(_get_txn_attr(txn, "transaction_type", "")).lower()
        if txn_type != "credit":
            continue

        desc = str(_get_txn_attr(txn, "description", ""))
        clean_desc = str(_get_txn_attr(txn, "cleaned_description", ""))
        full_text = f"{desc} {clean_desc}".strip()
        amount = float(_get_txn_attr(txn, "amount", 0.0))

        # Check interest pattern match
        is_match = bool(INTEREST_PATTERNS.search(full_text))

        # Category check if present
        cat = _get_txn_attr(txn, "category")
        cat_name = str(cat.name if hasattr(cat, "name") else cat).lower() if cat else ""
        if "interest" in cat_name:
            is_match = True

        if not is_match:
            continue

        # If not senior citizen, exclude term deposits from 80TTA (80TTA covers savings only)
        if not is_senior_citizen and TERM_DEPOSIT_PATTERNS.search(full_text):
            continue

        if amount > 0:
            total_interest += amount
            matched_txns.append({
                "date": str(_get_txn_attr(txn, "date", "")),
                "description": desc,
                "amount": round(amount, 2),
            })

    total_interest = round(total_interest, 2)
    eligible_sec = "80TTB" if is_senior_citizen else "80TTA"
    cap = 50000.0 if is_senior_citizen else 10000.0
    allowable_deduction = round(min(total_interest, cap), 2)

    prompt = (
        f"You received approximately ₹{total_interest:,.2f} in savings interest this year — "
        f"this must be reported as income, and you can claim up to ₹{cap:,.0f} "
        f"({'₹50,000 if senior citizen' if not is_senior_citizen else 'under Section 80TTB'}) "
        f"under 80TTA/80TTB."
    )

    return {
        "has_interest": (total_interest > 0),
        "total_interest": total_interest,
        "taxable_interest_income": total_interest,
        "eligible_section": eligible_sec,
        "cap": cap,
        "allowable_deduction": allowable_deduction,
        "transaction_count": len(matched_txns),
        "transactions": matched_txns,
        "prompt_message": prompt if total_interest > 0 else None,
    }


def detect_capital_gains_activity(
    transactions: List[Any],
) -> Dict[str, Any]:
    """
    Task 17.2: Scans transactions for mutual fund redemptions or broker payouts.
    SURFACES AN INFORMATIONAL FLAG ONLY.
    STRICT INVARIANT: NEVER ATTEMPTS TO COMPUTE CAPITAL GAINS.
    """
    flagged: List[Dict[str, Any]] = []

    for txn in transactions:
        txn_type = str(_get_txn_attr(txn, "transaction_type", "")).lower()
        if txn_type != "credit":
            continue

        desc = str(_get_txn_attr(txn, "description", ""))
        clean_desc = str(_get_txn_attr(txn, "cleaned_description", ""))
        full_text = f"{desc} {clean_desc}".strip()

        if CAPITAL_GAINS_PATTERNS.search(full_text):
            flagged.append({
                "date": str(_get_txn_attr(txn, "date", "")),
                "description": desc,
                "amount": round(float(_get_txn_attr(txn, "amount", 0.0)), 2),
            })

    has_cg = len(flagged) > 0
    warning = (
        "This may mean you have capital gains and need ITR-2, not ITR-1 — this tool doesn't compute "
        "capital gains, please consult further before filing."
    ) if has_cg else None

    return {
        "has_capital_gains_indicators": has_cg,
        "flagged_transactions_count": len(flagged),
        "flagged_transactions": flagged,
        "warning_message": warning,
        "recommended_itr_form": "ITR-2" if has_cg else "ITR-1",
    }


def detect_salary_arrears(
    transactions: List[Any],
) -> Dict[str, Any]:
    """
    Task 17.3: Detects an unusually large one-time salary-like credit inconsistent with
    the regular monthly pattern, or explicitly marked as arrears/pay revision.
    Flags it for checking Section 89 relief eligibility (via Form 10E).
    """
    salary_txns: List[Dict[str, Any]] = []

    for txn in transactions:
        txn_type = str(_get_txn_attr(txn, "transaction_type", "")).lower()
        if txn_type != "credit":
            continue

        desc = str(_get_txn_attr(txn, "description", ""))
        clean_desc = str(_get_txn_attr(txn, "cleaned_description", ""))
        full_text = f"{desc} {clean_desc}".strip()
        amount = float(_get_txn_attr(txn, "amount", 0.0))

        cat = _get_txn_attr(txn, "category")
        cat_name = str(cat.name if hasattr(cat, "name") else cat).lower() if cat else ""

        is_salary = bool(SALARY_PATTERNS.search(full_text)) or ("salary" in cat_name)
        is_arrears_word = bool(ARREARS_KEYWORDS.search(full_text))

        if is_salary or is_arrears_word:
            salary_txns.append({
                "date": str(_get_txn_attr(txn, "date", "")),
                "description": desc,
                "amount": amount,
                "explicit_arrears_keyword": is_arrears_word,
            })

    if not salary_txns:
        return {
            "has_arrears_indicator": False,
            "warning_message": None,
            "flagged_transactions": [],
            "regular_monthly_salary": 0.0,
        }

    amounts = [t["amount"] for t in salary_txns]
    median_sal = statistics.median(amounts) if amounts else 0.0

    flagged: List[Dict[str, Any]] = []
    for st in salary_txns:
        # Check explicit keyword or spike >= 1.75x of baseline salary
        is_spike = (len(amounts) >= 2 and median_sal > 0 and st["amount"] >= 1.75 * median_sal)
        if st["explicit_arrears_keyword"] or is_spike:
            flagged.append(st)

    has_arrears = len(flagged) > 0
    warning = None
    if has_arrears:
        primary = flagged[0]
        warning = (
            f"Detected an unusually large salary credit of ₹{primary['amount']:,.2f} on {primary['date']}. "
            "This may include salary arrears or unexpected pay revision. You should check eligibility "
            "for Section 89 relief (via Form 10E) rather than including it as ordinary income without comment."
        )

    return {
        "has_arrears_indicator": has_arrears,
        "warning_message": warning,
        "flagged_transactions": flagged,
        "regular_monthly_salary": round(median_sal, 2),
    }


def get_ais_26as_checklist() -> Dict[str, Any]:
    """
    Task 17.4: Generates statutory AIS (Annual Information Statement) and Form 26AS
    cross-check reconciliation checklist for the final tax report and PDF.
    """
    return {
        "notice_banner": (
            "Before filing, download your AIS and Form 26AS from the income tax portal "
            "and cross-check against this report."
        ),
        "portal_url": "https://www.incometax.gov.in",
        "checklist_items": [
            {
                "id": "tds_26as",
                "title": "Form 26AS TDS Verification",
                "description": (
                    "Cross-check tax deducted at source (TDS) in your Form 16 Part A against Part A "
                    "of Form 26AS to confirm all employer and bank TDS has been credited to your PAN."
                ),
            },
            {
                "id": "ais_interest_dividends",
                "title": "AIS Savings & Deposit Interest",
                "description": (
                    "Reconcile savings account interest, fixed deposit interest, and dividend payouts "
                    "listed in your Annual Information Statement (AIS / TIS) with this report."
                ),
            },
            {
                "id": "gross_salary_schedule",
                "title": "Gross Salary Consistency",
                "description": (
                    "Confirm total gross compensation reported matches or exceeds the salary income "
                    "in AIS (Schedule S) to avoid automated CPC defect notices."
                ),
            },
            {
                "id": "bank_prevalidation",
                "title": "Bank Account Pre-Validation for Direct Refund",
                "description": (
                    "Ensure your refund-eligible bank account is pre-validated and PAN-linked on the "
                    "income tax e-filing portal to receive direct electronic tax refunds."
                ),
            },
        ],
    }


def compute_filing_deadline_countdown(
    financial_year: str = "2025-2026",
    reference_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Task 17.5: Calculates remaining days until the non-audit salaried ITR filing deadline
    (July 31 of the Assessment Year).
    """
    today = reference_date or date.today()

    # Parse financial year (e.g., "2025-2026")
    parts = financial_year.split("-")
    try:
        start_year = int(parts[0])
        end_year = int(parts[1]) if len(parts) > 1 else start_year + 1
    except (ValueError, IndexError):
        start_year = 2025
        end_year = 2026

    # Assessment Year is (end_year) - (end_year + 1)
    ay_start = end_year
    ay_end = end_year + 1
    ay_str = f"{ay_start}-{ay_end}"

    # Salaried individual deadline: July 31 of Assessment Year
    deadline_date = date(ay_start, 7, 31)
    days_remaining = (deadline_date - today).days

    is_expired = days_remaining < 0

    if days_remaining > 0:
        status_msg = f"{days_remaining} days remaining to file your ITR (Deadline: 31 July {ay_start})"
    elif days_remaining == 0:
        status_msg = f"Today is the deadline to file your ITR! (31 July {ay_start})"
    else:
        status_msg = (
            f"The standard ITR filing deadline was 31 July {ay_start} ({abs(days_remaining)} days ago). "
            f"Filing a belated return under Section 139(4) may incur a late fee under Section 234F."
        )

    return {
        "financial_year": financial_year,
        "assessment_year": ay_str,
        "deadline_date": deadline_date.isoformat(),
        "days_remaining": days_remaining,
        "is_expired": is_expired,
        "status_message": status_msg,
    }


def compute_year_over_year_comparison_data(
    current_data: Dict[str, Any],
    prior_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Task 17.6: Compares current year's tax computation metrics against prior year's.
    Highlights key changes in income, deductions, and tax liabilities.
    """
    current_fy = current_data.get("financial_year", "2025-2026")
    has_prior = prior_data is not None

    if not has_prior:
        return {
            "current_financial_year": current_fy,
            "prior_financial_year": None,
            "has_prior_year_data": False,
            "metrics": {},
            "highlights": [f"Single year data available for {current_fy}."],
        }

    prior_fy = prior_data.get("financial_year", "2024-2025")

    curr_gross = float(current_data.get("gross_income", 0.0))
    prior_gross = float(prior_data.get("gross_income", 0.0))
    gross_delta = round(curr_gross - prior_gross, 2)
    gross_pct = round((gross_delta / prior_gross * 100.0), 1) if prior_gross > 0 else 0.0

    curr_old_tax = float(current_data.get("old_regime_total_liability", current_data.get("old_regime", {}).get("total_tax", 0.0)))
    prior_old_tax = float(prior_data.get("old_regime_total_liability", prior_data.get("old_regime", {}).get("total_tax", 0.0)))
    old_tax_delta = round(curr_old_tax - prior_old_tax, 2)

    curr_new_tax = float(current_data.get("new_regime_total_liability", current_data.get("new_regime", {}).get("total_tax", 0.0)))
    prior_new_tax = float(prior_data.get("new_regime_total_liability", prior_data.get("new_regime", {}).get("total_tax", 0.0)))
    new_tax_delta = round(curr_new_tax - prior_new_tax, 2)

    curr_rec = str(current_data.get("recommended_regime", "new")).lower()
    prior_rec = str(prior_data.get("recommended_regime", "new")).lower()

    curr_savings = float(current_data.get("tax_savings", 0.0))
    prior_savings = float(prior_data.get("tax_savings", 0.0))

    highlights: List[str] = []
    if gross_delta > 0:
        highlights.append(f"Gross annual income increased by ₹{gross_delta:,.2f} (+{gross_pct}%).")
    elif gross_delta < 0:
        highlights.append(f"Gross annual income decreased by ₹{abs(gross_delta):,.2f} ({gross_pct}%).")
    else:
        highlights.append("Gross annual income remained unchanged.")

    if curr_rec != prior_rec:
        highlights.append(f"Optimal tax regime changed from {prior_rec.upper()} to {curr_rec.upper()}.")
    else:
        highlights.append(f"Recommended regime remained {curr_rec.upper()}.")

    if curr_rec == "old":
        tax_diff = curr_old_tax - prior_old_tax
    else:
        tax_diff = curr_new_tax - prior_new_tax

    if tax_diff > 0:
        highlights.append(f"Effective tax liability increased by ₹{tax_diff:,.2f} compared to prior year.")
    elif tax_diff < 0:
        highlights.append(f"Effective tax liability reduced by ₹{abs(tax_diff):,.2f} compared to prior year.")

    return {
        "current_financial_year": current_fy,
        "prior_financial_year": prior_fy,
        "has_prior_year_data": True,
        "metrics": {
            "gross_income": {
                "current": curr_gross,
                "prior": prior_gross,
                "delta": gross_delta,
                "percentage_change": gross_pct,
            },
            "old_regime_liability": {
                "current": curr_old_tax,
                "prior": prior_old_tax,
                "delta": old_tax_delta,
            },
            "new_regime_liability": {
                "current": curr_new_tax,
                "prior": prior_new_tax,
                "delta": new_tax_delta,
            },
            "recommended_regime": {
                "current": curr_rec.upper(),
                "prior": prior_rec.upper(),
                "changed": (curr_rec != prior_rec),
            },
            "tax_savings": {
                "current": curr_savings,
                "prior": prior_savings,
                "delta": round(curr_savings - prior_savings, 2),
            },
        },
        "highlights": highlights,
    }

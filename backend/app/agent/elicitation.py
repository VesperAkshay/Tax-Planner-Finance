"""
Proactive Stateful Elicitation Engine (v1.1 Phase 13).

Provides:
- 13.1 Canonical ordering and proactive question templates for all catalog sections.
- 13.2 Automatic conditional skip rules (e.g., skip 80GG if salary slip has HRA).
- 13.3 Proactive question formulation grounded in statutory rules and RAG citations.
- 13.4 Response classification (declared amount vs not_applicable).
- 13.5 Completion gate detection (intercepting short-circuit requests).
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.agent.state import ElicitationAnswer, ElicitationState, TaxPlanningState

# Ordered sequence for structured elicitation
CANONICAL_SECTIONS_ORDER: List[str] = [
    "80C",
    "80CCD(1B)",
    "80CCD(2)",
    "80D",
    "80D (parents)",
    "10(13A)",
    "80GG",
    "24(b)",
    "80EEA",
    "80E",
    "80G",
    "80GGC",
    "80TTA",
    "80TTB",
    "80DD",
    "80DDB",
    "80U",
    "10(5)",
]

# Proactive Question Templates for Each Section
SECTION_QUESTIONS: Dict[str, str] = {
    "80C": (
        "Let's examine **Section 80C**. Do you make investments in PPF, EPF/VPF, ELSS tax-saving mutual funds, "
        "life insurance premiums, home loan principal repayment, Sukanya Samriddhi, or children's tuition fees? "
        "(Maximum statutory limit: ₹1,50,000). Please state your total annual amount or reply 'No'."
    ),
    "80CCD(1B)": (
        "Under **Section 80CCD(1B)**, you can claim an additional deduction of up to ₹50,000 for voluntary self-contributions "
        "to the National Pension Scheme (NPS Tier 1), over and above Section 80C. Did you contribute to NPS on your own?"
    ),
    "80CCD(2)": (
        "**Section 80CCD(2)** covers your employer's contribution to your NPS account. This deduction is especially valuable "
        "because it is eligible under **BOTH Old and New Tax Regimes** (up to 14% of Basic salary). "
        "Does your employer contribute to NPS on your behalf?"
    ),
    "80D": (
        "Under **Section 80D**, you can claim medical insurance premiums paid for yourself, spouse, and dependent children "
        "(up to ₹25,000, or ₹50,000 if you are a senior citizen), plus up to ₹5,000 for preventive health checkups. "
        "Did you pay health insurance premiums for your family?"
    ),
    "80D (parents)": (
        "Under **Section 80D (Parents)**, you can claim an additional deduction for health insurance premiums paid for your parents "
        "(up to ₹25,000, or ₹50,000 if your parents are senior citizens aged 60+). Did you pay health insurance premiums for parents?"
    ),
    "10(13A)": (
        "Under **Section 10(13A)**, you are entitled to House Rent Allowance (HRA) exemption if you live in rented accommodation "
        "and receive HRA. Do you pay rent for your home? If yes, what is your monthly or annual rent, and is the city a metro (Delhi, Mumbai, Kolkata, Chennai)?"
    ),
    "80GG": (
        "Under **Section 80GG**, individuals who do not receive HRA from their employer can claim a deduction for rent paid "
        "up to ₹60,000 per annum. Did you pay house rent during this financial year?"
    ),
    "24(b)": (
        "Under **Section 24(b)**, you can claim a deduction of up to ₹2,00,000 for interest paid on a home loan for a self-occupied "
        "house property. Did you pay home loan interest this year?"
    ),
    "80EEA": (
        "Under **Section 80EEA**, first-time home buyers can claim an additional deduction of up to ₹1,50,000 on home loan interest "
        "for affordable housing sanctioned between 2019 and 2022 (over and above Section 24b). Do you qualify for Section 80EEA?"
    ),
    "80E": (
        "Under **Section 80E**, there is no upper monetary limit on deductions for interest paid on an education loan taken for higher "
        "studies of yourself, spouse, or children. Did you pay education loan interest this year?"
    ),
    "80G": (
        "Under **Section 80G**, donations to eligible charitable trusts, PM CARES, or relief funds qualify for a 50% or 100% tax deduction "
        "with valid 80G receipts. Did you make any eligible donations this year?"
    ),
    "80GGC": (
        "Under **Section 80GGC**, contributions made via bank transfer/cheque to registered political parties or electoral trusts are "
        "100% deductible. Did you make any political contributions?"
    ),
    "80TTA": (
        "Under **Section 80TTA**, interest income earned from savings bank accounts is deductible up to ₹10,000. "
        "Did you earn savings bank interest this year?"
    ),
    "80TTB": (
        "Under **Section 80TTB**, senior citizens (age 60+) can claim a deduction of up to ₹50,000 on interest income from savings "
        "and fixed deposits. Did you earn interest income this year?"
    ),
    "80DD": (
        "Under **Section 80DD**, individuals supporting a dependent family member with a certified disability can claim a fixed deduction "
        "of ₹75,000 (or ₹1,25,000 for severe disability >= 80%). Do you have a dependent with a disability?"
    ),
    "80DDB": (
        "Under **Section 80DDB**, medical treatment expenses for specified chronic diseases (cancer, chronic kidney disease, etc.) are "
        "deductible up to ₹40,000 (₹1,00,000 for senior citizens). Did you incur expenses for specified medical ailments?"
    ),
    "80U": (
        "Under **Section 80U**, a resident individual certified with a disability can claim a direct deduction of ₹75,000 "
        "(or ₹1,25,000 for severe disability >= 80%). Are you certified with a disability under Section 80U?"
    ),
    "10(5)": (
        "Under **Section 10(5)**, Leave Travel Allowance (LTA) received from your employer is exempt against actual domestic travel "
        "ticket expenses for two journeys in a 4-year block. Did you incur eligible travel expenses for LTA exemption?"
    ),
}


def evaluate_auto_skips(state: TaxPlanningState, catalog_sections: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Evaluates statutory skip rules automatically on conversation start (Task 13.2).
    Returns a dictionary mapping section_code -> machine-generated skip reason.
    """
    skips: Dict[str, str] = {}
    sections = catalog_sections or CANONICAL_SECTIONS_ORDER

    # 1. HRA vs Section 80GG mutual exclusion
    slip = state.salary_slip_data or {}
    slip_hra = float(slip.get("hra", 0.0))
    has_hra = state.has_hra_component and (slip_hra > 0.0 or bool(state.declared_deductions.get("hra")))

    if has_hra:
        if "80GG" in sections:
            skips["80GG"] = (
                f"Salary slip includes an HRA component (₹{slip_hra:,.2f}); "
                "Section 80GG statutorily applies only when no HRA is received from employer."
            )
    else:
        if "10(13A)" in sections:
            skips["10(13A)"] = "Salary slip does not include an HRA component; Section 10(13A) exemption is not applicable."

    # 2. Section 80TTA vs 80TTB (Senior Citizen Mutual Exclusion)
    is_senior = bool(
        state.is_senior_citizen
        or (
            state.user_profile
            and (
                state.user_profile.get("is_senior_citizen")
                or state.user_profile.get("age", 0) >= 60
            )
        )
    )
    if is_senior:
        if "80TTA" in sections:
            skips["80TTA"] = "Section 80TTB replaces Section 80TTA for senior citizens (age 60+)."
    else:
        if "80TTB" in sections:
            skips["80TTB"] = "Section 80TTB is applicable only to senior citizens (age 60+). Section 80TTA applies instead."

    # 3. Dependent Parents Health Insurance
    if not state.has_dependent_parents:
        if "80D (parents)" in sections:
            skips["80D (parents)"] = "User indicated no dependent parents."

    return skips


def is_short_circuit_attempt(message: str) -> bool:
    """
    Detects if user is attempting to bypass elicitation to view tax calculation early (Task 13.5).
    """
    if not message:
        return False
    msg = message.strip().lower()
    patterns = [
        r"\b(?:just|now)?\s*(?:calculate|compute|show|tell|give)\s*(?:me)?\s*(?:my)?\s*tax\b",
        r"\bshow\s*(?:the)?\s*report\b",
        r"\bskip\s*(?:all|everything|to\s*the\s*end|ahead)\b",
        r"\bcalculate\s*now\b",
        r"\bwhat\s*(?:is)?\s*my\s*tax\b",
        r"\bjust\s*the\s*tax\b",
        r"\bgo\s*to\s*tax\b",
        r"\bfinal\s*tax\b",
        r"\bhow\s*much\s*tax\b",
        r"\btax\s*liability\b",
        r"\btax\s*(?:i\s*)?owe\b",
        r"\bgive\s*(?:me)?\s*(?:the)?\s*recommendation\b",
    ]
    return any(re.search(pat, msg) for pat in patterns)


def is_explicit_rejection(message: str) -> bool:
    """
    Detects if user explicitly indicates 'not applicable' / 'no' / 'none' / 'zero'.
    """
    if not message:
        return False
    msg = message.strip().lower()

    # Exact matches or short rejections
    rejection_phrases = {
        "no", "nope", "none", "nil", "n/a", "na", "not applicable", "dont have",
        "don't have", "zero", "0", "skip", "no investments", "no insurance",
        "nothing", "not eligible", "not claiming", "n.a.", "no donation", "no rent",
    }
    if msg in rejection_phrases:
        return True

    # Regex patterns for natural language negation
    negation_patterns = [
        r"^(?:no|none|nil|nope|na|n/a)\b",
        r"\bi\s*(?:do\s*not|don't)\s*(?:have|pay|claim|invest)\b",
        r"\bnot\s*applicable\b",
        r"\b(?:zero|0)\s*(?:inr|rs\.?|rupees)?$",
    ]
    return any(re.search(pat, msg) for pat in negation_patterns)


def parse_inr_value(text: str) -> Optional[float]:
    """Parses Indian Rupee amounts from natural language."""
    cleaned = text.replace(",", "").replace("₹", "").strip().lower()
    m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:l|lac|lakh|lakhs)", cleaned)
    if m_lakh:
        return float(m_lakh.group(1)) * 100000.0
    m_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", cleaned)
    if m_k:
        return float(m_k.group(1)) * 1000.0
    m_num = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if m_num:
        val = float(m_num.group(1))
        # Ignore trivial numbers like 0 or single digits unless formatted as currency
        if val > 0:
            return val
    return None


def parse_elicitation_response(
    message: str,
    section_code: str,
) -> Tuple[str, float, Optional[Dict[str, Any]]]:
    """
    Classifies a user's response to an elicited deduction section (Task 13.4).
    Returns (status, amount, metadata).
    status: 'declared' | 'not_applicable' | 'unclear'
    """
    if not message:
        return "unclear", 0.0, None

    if is_explicit_rejection(message):
        return "not_applicable", 0.0, None

    msg = message.strip().lower()

    # Special handling for HRA / Section 80GG rent
    if section_code in ("10(13A)", "80GG"):
        is_metro = any(c in msg for c in ["mumbai", "delhi", "kolkata", "chennai", "metro"])
        amount = parse_inr_value(message)
        if amount is not None and amount > 0:
            # Annualize if monthly rent indicated
            if "month" in msg or "pm" in msg or amount <= 120000:
                annual_rent = amount * 12.0
            else:
                annual_rent = amount
            return "declared", annual_rent, {"rent_paid_annual": annual_rent, "is_metro": is_metro}
        return "unclear", 0.0, None

    # General deduction parsing
    amount = parse_inr_value(message)
    if amount is not None:
        # Cap Section 80C to 150,000
        if section_code == "80C":
            amount = min(amount, 150000.0)
        elif section_code == "80CCD(1B)":
            amount = min(amount, 50000.0)
        elif section_code in ("80D", "80D (parents)"):
            amount = min(amount, 100000.0)
        elif section_code == "24(b)":
            amount = min(amount, 200000.0)
        elif section_code == "80EEA":
            amount = min(amount, 150000.0)
        elif section_code == "80TTA":
            amount = min(amount, 10000.0)
        elif section_code == "80TTB":
            amount = min(amount, 50000.0)

        return "declared", amount, None

    # Check for affirmative without clear amount (e.g. "yes I have 80C")
    if any(w in msg for w in ["yes", "yeah", "yep", "i have", "eligible"]):
        # Default to max standard cap or prompt clarification
        if section_code == "80C":
            return "declared", 150000.0, {"inferred_full_cap": True}

    return "unclear", 0.0, None

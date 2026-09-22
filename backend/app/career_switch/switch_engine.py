"""
Career Switch & Offer Letter Decoder Engine.
Provides deterministic financial and statutory models for:
1. Offer Letter CTC Breakdown & Real Monthly In-Hand Cash calculation.
2. Hidden Traps & Red-Flag Detection (Gratuity vesting, bonus clawback, Special Allowance tax penalty).
3. Mid-Year Switch Tax Simulation (The Dual-Employer Double Standard Deduction & Slab Cliff Trap).
4. Section 234B & 234C Interest Shortfall Computation.
5. Statutory Form 12B Particulars Generation.
6. AI Salary Negotiation & Tax-Efficient Restructuring Playbook.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math

from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.rules_loader import load_tax_rules


@dataclass
class CTCBreakdown:
    annual_ctc: float
    basic: float
    hra: float
    special_allowance: float
    gratuity_annual: float
    employer_pf_annual: float
    employee_pf_annual: float
    medical_insurance_annual: float
    variable_pay: float
    joining_bonus: float
    bonus_clawback_months: int
    esop_annual: float

    # Calculated outputs
    guaranteed_fixed_gross_annual: float
    monthly_fixed_gross: float
    monthly_basic: float
    monthly_hra: float
    monthly_special_allowance: float
    monthly_employee_pf: float
    monthly_professional_tax: float
    monthly_tds: float
    guaranteed_monthly_in_hand: float
    annual_guaranteed_in_hand: float
    annual_tax_liability: float
    effective_tax_rate: float
    retirals_total_annual: float
    at_risk_total_annual: float


def decode_offer_ctc(
    ctc: float,
    basic: Optional[float] = None,
    hra: Optional[float] = None,
    special_allowance: Optional[float] = None,
    variable_pay: float = 0.0,
    joining_bonus: float = 0.0,
    bonus_clawback_months: int = 12,
    esop_annual: float = 0.0,
    gratuity_included: bool = True,
    employer_pf_included: bool = True,
    medical_insurance_annual: float = 0.0,
    rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Decodes an annual Cost-to-Company (CTC) offer into its real-world cash and statutory breakdown.
    Calculates guaranteed take-home pay, identifies offer letter traps, and suggests tax-saving restructures.
    """
    if rules is None:
        rules = load_tax_rules()

    clean_ctc = max(0.0, float(ctc))
    var_pay = max(0.0, float(variable_pay))
    join_bonus = max(0.0, float(joining_bonus))
    esops = max(0.0, float(esop_annual))
    med_ins = max(0.0, float(medical_insurance_annual))

    # Basic defaults to 40% of CTC if not provided
    if basic is not None and basic > 0:
        clean_basic = float(basic)
    else:
        # Standard corporate benchmark: 40% of CTC
        clean_basic = round(clean_ctc * 0.40, 2)

    # Gratuity: Statutory Payment of Gratuity Act formula = 15/26 days per year of basic
    # Annually = Basic * (15/26) / 12 * 12 = 4.8077% of Basic
    if gratuity_included:
        gratuity = round(clean_basic * (15.0 / 26.0) / 12.0 * 12.0, 2)
    else:
        gratuity = 0.0

    # Employer PF: 12% of Basic
    if employer_pf_included:
        employer_pf = round(clean_basic * 0.12, 2)
    else:
        employer_pf = 0.0

    # Retirals and at-risk sums
    retirals_annual = round(gratuity + employer_pf + med_ins, 2)
    at_risk_annual = round(var_pay + esops, 2)

    # HRA: default to 40% of Basic (typical non-metro/standard benchmark)
    if hra is not None and hra >= 0:
        clean_hra = float(hra)
    else:
        clean_hra = round(clean_basic * 0.40, 2)

    # Special Allowance: residual of fixed gross if not specified
    remaining_for_fixed = max(0.0, clean_ctc - retirals_annual - at_risk_annual)
    if special_allowance is not None and special_allowance >= 0:
        clean_special = float(special_allowance)
    else:
        clean_special = max(0.0, round(remaining_for_fixed - clean_basic - clean_hra, 2))

    guaranteed_fixed_gross = round(clean_basic + clean_hra + clean_special, 2)
    monthly_fixed_gross = round(guaranteed_fixed_gross / 12.0, 2)
    monthly_basic = round(clean_basic / 12.0, 2)
    monthly_hra = round(clean_hra / 12.0, 2)
    monthly_special = round(clean_special / 12.0, 2)

    # Employee PF: 12% of Basic deducted from pay
    employee_pf_annual = round(clean_basic * 0.12, 2)
    monthly_employee_pf = round(employee_pf_annual / 12.0, 2)

    # Professional Tax: standard ₹200/month (₹2,400/yr in states like Karnataka, Maharashtra, etc.)
    monthly_pt = 200.0
    annual_pt = 2400.0

    # Compute annual tax on guaranteed fixed gross under New Regime FY 2025-26
    tax_result = compute_new_regime_tax(guaranteed_fixed_gross, rules, is_salaried=True)
    annual_tax = float(tax_result["total_tax"])
    monthly_tds = round(annual_tax / 12.0, 2)

    # Guaranteed In-Hand Take-Home
    guaranteed_monthly_in_hand = max(
        0.0, round(monthly_fixed_gross - monthly_employee_pf - monthly_pt - monthly_tds, 2)
    )
    annual_guaranteed_in_hand = round(guaranteed_monthly_in_hand * 12.0, 2)

    # Red-Flag Traps Detection
    traps: List[Dict[str, Any]] = []

    # 1. Gratuity Lock
    if gratuity > 0:
        traps.append({
            "code": "GRATUITY_LOCK",
            "title": f"₹{int(gratuity):,} Gratuity Locked in Paper CTC",
            "severity": "medium",
            "description": (
                f"Your employer counts ₹{int(gratuity):,}/year as part of your CTC. Under the Payment of Gratuity Act 1972, "
                "gratuity is legally payable ONLY if you complete 5 continuous years with this company. "
                "If you switch jobs earlier, this money is forfeited and retained 100% by the company."
            ),
            "amount": gratuity,
        })

    # 2. Special Allowance Tax Penalty
    if clean_ctc > 0 and (clean_special / clean_ctc) > 0.30:
        pct = round((clean_special / clean_ctc) * 100)
        traps.append({
            "code": "SPECIAL_ALLOWANCE_TRAP",
            "title": f"Special Allowance Tax Sinkhole ({pct}% of CTC)",
            "severity": "high",
            "description": (
                f"₹{int(clean_special):,} of your salary is designated as 'Special Allowance'. Unlike Basic (which qualifies for PF) "
                "or HRA (which qualifies for rent exemption), Special Allowance has zero statutory tax exemptions. Every rupee will be taxed at your highest slab rate."
            ),
            "amount": clean_special,
        })

    # 3. Variable Pay Volatility
    if var_pay > 0:
        var_pct = round((var_pay / clean_ctc) * 100) if clean_ctc > 0 else 0
        traps.append({
            "code": "VARIABLE_PAY_AT_RISK",
            "title": f"₹{int(var_pay):,} Variable Pay At-Risk ({var_pct}% of CTC)",
            "severity": "high",
            "description": (
                f"This portion is not guaranteed monthly cash. In most Indian corporate policies, variable pay is tied to company EBITDA "
                "and relative bell-curve ratings. Do not budget fixed EMI, rent, or living expenses against this money."
            ),
            "amount": var_pay,
        })

    # 4. Joining Bonus Clawback Lock-In
    if join_bonus > 0:
        traps.append({
            "code": "CLAWBACK_RISK",
            "title": f"₹{int(join_bonus):,} Joining Bonus Clawback",
            "severity": "medium",
            "description": (
                f"Joining bonuses are taxed upfront in the month of payout. Clause agreements usually stipulate a {bonus_clawback_months}-month "
                "lock-in. If you resign before then, you must repay the full gross bonus out of pocket."
            ),
            "amount": join_bonus,
        })

    # AI Salary Negotiation & Restructuring Playbook
    # Opportunity 1: Employer NPS under 80CCD(2) (tax-free up to 14% of Basic in New Regime)
    potential_80ccd2_monthly = round((clean_basic / 12.0) * 0.14, 2)
    potential_80ccd2_annual = round(potential_80ccd2_monthly * 12.0, 2)
    tax_saved_80ccd2 = round(potential_80ccd2_annual * 0.312, 2)  # assuming 30% slab + 4% cess

    # Opportunity 2: Broadband & Telephone reimbursement (₹3,000/mo = ₹36,000/yr tax-free)
    broadband_annual = 36000.0
    tax_saved_broadband = round(broadband_annual * 0.312, 2)

    total_potential_tax_saved = round(tax_saved_80ccd2 + tax_saved_broadband, 2)

    negotiation_email = (
        f"Subject: Request for Tax-Optimized Salary Structure Component Adjustment - [Your Name]\n\n"
        f"Dear HR Team,\n\n"
        f"Thank you for the offer letter for the [Role Name] role. I am very excited to join the team.\n\n"
        f"While reviewing the CTC Annexure, I noticed that ₹{int(clean_special):,} is currently assigned to 'Special Allowance'. "
        f"At zero additional cost to the organization, could we please restructure this component into tax-efficient statutory benefits as follows?\n\n"
        f"1. Employer NPS (Section 80CCD(2)): Allocate 14% of Basic (₹{int(potential_80ccd2_monthly):,}/month) to corporate NPS.\n"
        f"2. Broadband & Telephone Allowance: Allocate ₹3,000/month as official communication reimbursement.\n\n"
        f"This adjustment preserves the exact same Total CTC of ₹{int(clean_ctc):,}, while optimizing net disposable compensation under the New Tax Regime.\n\n"
        f"Looking forward to your favorable response.\n\n"
        f"Best regards,\n[Your Name]"
    )

    return {
        "annual_ctc": clean_ctc,
        "components": {
            "basic": clean_basic,
            "hra": clean_hra,
            "special_allowance": clean_special,
            "gratuity_annual": gratuity,
            "employer_pf_annual": employer_pf,
            "employee_pf_annual": employee_pf_annual,
            "medical_insurance_annual": med_ins,
            "variable_pay": var_pay,
            "joining_bonus": join_bonus,
            "esop_annual": esops,
        },
        "monthly_breakdown": {
            "fixed_gross": monthly_fixed_gross,
            "basic": monthly_basic,
            "hra": monthly_hra,
            "special_allowance": monthly_special,
            "employee_pf_deduction": monthly_employee_pf,
            "professional_tax": monthly_pt,
            "monthly_tds_tax": monthly_tds,
            "guaranteed_in_hand": guaranteed_monthly_in_hand,
        },
        "annual_totals": {
            "guaranteed_fixed_gross": guaranteed_fixed_gross,
            "annual_in_hand": annual_guaranteed_in_hand,
            "annual_tax": annual_tax,
            "effective_tax_rate_pct": tax_result.get("effective_tax_rate", 0.0),
            "retirals_total": retirals_annual,
            "at_risk_total": at_risk_annual,
        },
        "traps_detected": traps,
        "negotiation_playbook": {
            "suggested_80ccd2_monthly": potential_80ccd2_monthly,
            "suggested_broadband_monthly": 3000.0,
            "annual_tax_saved": total_potential_tax_saved,
            "counter_proposal_email": negotiation_email,
        },
    }


def simulate_midyear_switch(
    company_a_months: int,
    company_a_gross: float,
    company_a_tds: float,
    company_a_epf: float,
    company_b_months: int,
    company_b_monthly_gross: float,
    rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Simulates a mid-year job switch between Company A and Company B.
    Calculates the lethal "Double Standard Deduction & Slab Cliff Trap" that creates
    massive surprise tax demands in July, computes Section 234B/C interest,
    and generates Form 12B remediation.
    """
    if rules is None:
        rules = load_tax_rules()

    months_a = max(1, min(11, int(company_a_months)))
    months_b = max(1, 12 - months_a)

    gross_a = max(0.0, float(company_a_gross))
    tds_a = max(0.0, float(company_a_tds))
    epf_a = max(0.0, float(company_a_epf))

    b_monthly_gross = max(0.0, float(company_b_monthly_gross))
    gross_b = round(b_monthly_gross * months_b, 2)

    # 1. Standalone Scenario: What Company B calculates if you DO NOT submit Form 12B
    # Company B treats its gross_b as an independent period or annualizes it naively.
    # Under standard payroll software, Company B applies its OWN ₹75,000 standard deduction and 0% slab.
    res_b_standalone = compute_new_regime_tax(gross_b, rules, is_salaried=True)
    tds_b_standalone = float(res_b_standalone["total_tax"])

    total_tds_deducted_without_12b = round(tds_a + tds_b_standalone, 2)

    # 2. True Statutory Combined Liability: What the Income Tax Department calculates in July ITR
    total_combined_gross = round(gross_a + gross_b, 2)
    # Exactly ONE standard deduction of ₹75,000 applies across the whole financial year
    res_combined_true = compute_new_regime_tax(total_combined_gross, rules, is_salaried=True)
    true_annual_tax = float(res_combined_true["total_tax"])

    # 3. The Shock: TDS Shortfall
    tds_shortfall = max(0.0, round(true_annual_tax - total_tds_deducted_without_12b, 2))

    # Section 234B & 234C Penalties:
    # Under Section 234B, if total tax deducted/paid before March 31 is < 90% of assessed tax,
    # interest of 1% per month applies on the shortfall from April 1 to the date of filing (e.g. July 31 = 4 months).
    if total_tds_deducted_without_12b < (0.90 * true_annual_tax) and tds_shortfall > 0:
        interest_234b = round(tds_shortfall * 0.01 * 4, 2)  # 4%
    else:
        interest_234b = 0.0

    # Section 234C: Deferment of advance tax installments (standard approximate average ~1.5%)
    if tds_shortfall > 10000:
        interest_234c = round(tds_shortfall * 0.015, 2)
    else:
        interest_234c = 0.0

    total_july_surprise_demand = round(tds_shortfall + interest_234b + interest_234c, 2)

    # 4. Remediation: What Company B SHOULD deduct if Form 12B is submitted
    # Tax already paid at Company A = tds_a
    remaining_tax_to_collect = max(0.0, round(true_annual_tax - tds_a, 2))
    recommended_monthly_tds_company_b = round(remaining_tax_to_collect / months_b, 2)

    # Form 12B Summary Text for Employee
    form_12b_summary = {
        "statement_period": f"Company A ({months_a} months) -> Company B ({months_b} months)",
        "gross_salary_company_a": gross_a,
        "tds_deducted_company_a": tds_a,
        "provident_fund_company_a": epf_a,
        "gross_salary_company_b_expected": gross_b,
        "total_annual_combined_income": total_combined_gross,
        "statutory_form_12b_rule": "Rule 26A of Income Tax Rules, 1962 (Section 192(2))",
    }

    return {
        "timeline": {
            "company_a_months": months_a,
            "company_b_months": months_b,
        },
        "incomes": {
            "company_a_gross": gross_a,
            "company_b_gross": gross_b,
            "total_combined_gross": total_combined_gross,
        },
        "without_form_12b": {
            "company_a_tds": tds_a,
            "company_b_projected_tds": tds_b_standalone,
            "total_tds_collected": total_tds_deducted_without_12b,
        },
        "true_statutory_liability": {
            "total_tax_due": true_annual_tax,
            "effective_tax_rate_pct": res_combined_true.get("effective_tax_rate", 0.0),
        },
        "the_tax_shock": {
            "tds_shortfall": tds_shortfall,
            "section_234b_interest": interest_234b,
            "section_234c_interest": interest_234c,
            "total_july_demand": total_july_surprise_demand,
            "has_critical_shortfall": tds_shortfall > 15000,
        },
        "with_form_12b": {
            "remaining_tax_for_company_b": remaining_tax_to_collect,
            "adjusted_monthly_tds": recommended_monthly_tds_company_b,
            "july_tax_surprise": 0.0,
            "interest_saved": round(interest_234b + interest_234c, 2),
        },
        "form_12b_particulars": form_12b_summary,
    }


def compare_two_offers(
    current_ctc: float,
    offer_a_ctc: float,
    offer_b_ctc: Optional[float] = None,
    rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compares current compensation against Offer A and optional Offer B
    on pure monthly in-hand take-home cash after tax and statutory deductions.
    """
    if rules is None:
        rules = load_tax_rules()

    curr_decoded = decode_offer_ctc(current_ctc, rules=rules)
    offer_a_decoded = decode_offer_ctc(offer_a_ctc, rules=rules)

    curr_inhand = curr_decoded["monthly_breakdown"]["guaranteed_in_hand"]
    offer_a_inhand = offer_a_decoded["monthly_breakdown"]["guaranteed_in_hand"]

    inhand_diff_a = round(offer_a_inhand - curr_inhand, 2)
    inhand_hike_pct_a = round((inhand_diff_a / curr_inhand * 100), 1) if curr_inhand > 0 else 0.0
    paper_ctc_hike_pct_a = round(((offer_a_ctc - current_ctc) / current_ctc * 100), 1) if current_ctc > 0 else 0.0

    result: Dict[str, Any] = {
        "current": {
            "ctc": current_ctc,
            "monthly_in_hand": curr_inhand,
            "annual_in_hand": curr_decoded["annual_totals"]["annual_in_hand"],
            "annual_tax": curr_decoded["annual_totals"]["annual_tax"],
        },
        "offer_a": {
            "ctc": offer_a_ctc,
            "monthly_in_hand": offer_a_inhand,
            "annual_in_hand": offer_a_decoded["annual_totals"]["annual_in_hand"],
            "annual_tax": offer_a_decoded["annual_totals"]["annual_tax"],
            "paper_ctc_hike_pct": paper_ctc_hike_pct_a,
            "real_in_hand_hike_pct": inhand_hike_pct_a,
            "monthly_cash_gain": inhand_diff_a,
        },
    }

    if offer_b_ctc is not None and offer_b_ctc > 0:
        offer_b_decoded = decode_offer_ctc(offer_b_ctc, rules=rules)
        offer_b_inhand = offer_b_decoded["monthly_breakdown"]["guaranteed_in_hand"]
        inhand_diff_b = round(offer_b_inhand - curr_inhand, 2)
        inhand_hike_pct_b = round((inhand_diff_b / curr_inhand * 100), 1) if curr_inhand > 0 else 0.0
        paper_ctc_hike_pct_b = round(((offer_b_ctc - current_ctc) / current_ctc * 100), 1) if current_ctc > 0 else 0.0

        result["offer_b"] = {
            "ctc": offer_b_ctc,
            "monthly_in_hand": offer_b_inhand,
            "annual_in_hand": offer_b_decoded["annual_totals"]["annual_in_hand"],
            "annual_tax": offer_b_decoded["annual_totals"]["annual_tax"],
            "paper_ctc_hike_pct": paper_ctc_hike_pct_b,
            "real_in_hand_hike_pct": inhand_hike_pct_b,
            "monthly_cash_gain": inhand_diff_b,
        }

    return result

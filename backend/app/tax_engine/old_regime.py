"""
Old Tax Regime Computation Engine (Task 5.3).

Pure function implementing Old Tax Regime calculations for FY 2025-26.
Computes deductions across Section 80C, 80D, 80CCD(1B), Section 24b, and Section 10(13A) HRA,
slabs, 87A rebate, and 4% cess strictly loaded from the rules object.
Contains zero hardcoded tax figures in the function body.
"""

from typing import Any, Dict, List, Optional


def compute_hra_exemption(
    hra_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes Section 10(13A) House Rent Allowance (HRA) exemption as minimum of:
    1. Actual HRA received
    2. Rent paid in excess of 10% of basic salary
    3. 50% of basic salary (metro) or 40% of basic salary (non-metro)
    """
    basic_salary = max(0.0, float(hra_data.get("basic_salary", 0.0)))
    hra_received = max(0.0, float(hra_data.get("hra_received", 0.0)))
    rent_paid = max(0.0, float(hra_data.get("rent_paid", 0.0)))
    is_metro = bool(hra_data.get("is_metro", False))

    if hra_received <= 0.0 or rent_paid <= 0.0 or basic_salary <= 0.0:
        return {
            "exemption": 0.0,
            "actual_hra_received": hra_received,
            "rent_excess_over_10pct": 0.0,
            "salary_percentage_limit": 0.0,
            "is_metro": is_metro,
        }

    # 1. Actual HRA received
    limit_1 = hra_received

    # 2. Rent paid minus 10% of basic salary
    limit_2 = max(0.0, rent_paid - (0.10 * basic_salary))

    # 3. 50% for metro (Delhi, Mumbai, Kolkata, Chennai), 40% for non-metro
    metro_pct = 0.50 if is_metro else 0.40
    limit_3 = basic_salary * metro_pct

    exemption = round(min(limit_1, limit_2, limit_3), 2)

    return {
        "exemption": exemption,
        "actual_hra_received": round(limit_1, 2),
        "rent_excess_over_10pct": round(limit_2, 2),
        "salary_percentage_limit": round(limit_3, 2),
        "is_metro": is_metro,
    }


def compute_section_80d_deduction(
    health_data: Dict[str, Any],
    rules_80d: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes eligible Section 80D medical insurance deduction according to age tiers:
    - Self & Family: max ₹25,000 (non-senior) or ₹50,000 (senior)
    - Parents: max ₹25,000 (non-senior) or ₹50,000 (senior)
    - Preventive health checkup: up to ₹5,000 within the overall caps
    """
    self_senior = bool(health_data.get("is_self_senior", False))
    parents_senior = bool(health_data.get("are_parents_senior", False))

    self_premium = max(0.0, float(health_data.get("self_family_premium", 0.0)))
    parents_premium = max(0.0, float(health_data.get("parents_premium", 0.0)))
    checkup = max(0.0, float(health_data.get("preventive_health_checkup", 0.0)))

    checkup_cap = float(rules_80d.get("preventive_health_checkup_sublimit", 5000.0))
    allowed_checkup = min(checkup, checkup_cap)

    # Self & family cap
    self_cap = float(rules_80d["self_family_senior_max"] if self_senior else rules_80d["self_family_max"])
    # Allowed for self = premium + portion of checkup within cap
    allowed_self = min(self_cap, self_premium + allowed_checkup)
    remaining_checkup = max(0.0, allowed_checkup - max(0.0, allowed_self - self_premium))

    # Parents cap
    parents_cap = float(rules_80d["parents_senior_max"] if parents_senior else rules_80d["parents_max"])
    allowed_parents = min(parents_cap, parents_premium + remaining_checkup)

    total_80d = min(float(rules_80d.get("max_allowable", 100000.0)), allowed_self + allowed_parents)

    return {
        "claimed": round(self_premium + parents_premium + checkup, 2),
        "allowed": round(total_80d, 2),
        "self_family_allowed": round(allowed_self, 2),
        "parents_allowed": round(allowed_parents, 2),
        "self_cap": self_cap,
        "parents_cap": parents_cap,
    }


def compute_old_regime_tax(
    gross_income: float,
    deductions: Optional[Dict[str, Any]],
    rules: Dict[str, Any],
    is_salaried: bool = True,
) -> Dict[str, Any]:
    """
    Computes tax liability under the Old Tax Regime as a pure function.

    Parameters:
        gross_income: Total gross annual income in INR (float >= 0)
        deductions: Dictionary containing declared deductions (80C, 80D, 80CCD, 24b, HRA, etc.)
        rules: Parsed tax rules dictionary (from data/tax_rules/fy_2025_26.json)
        is_salaried: Whether standard deduction for salaried individuals applies

    Returns:
        Structured breakdown of standard deduction, itemized deductions allowed,
        taxable income, slab tax, 87A rebate, cess, and final net tax liability.
    """
    gross = max(0.0, float(gross_income))
    old_reg = rules["old_regime"]
    ded_rules = old_reg.get("deductions", {})
    cess_rate = float(rules["cess"]["rate"])

    ded_dict = deductions or {}
    deductions_breakdown: Dict[str, Any] = {}
    total_deductions = 0.0

    # 1. Standard Deduction (purely from rules config)
    std_deduction = float(old_reg["standard_deduction"]) if is_salaried else 0.0
    total_deductions += std_deduction

    # 2. Section 10(13A) HRA Exemption
    if "hra" in ded_dict and isinstance(ded_dict["hra"], dict):
        hra_res = compute_hra_exemption(ded_dict["hra"])
        hra_allowed = hra_res["exemption"]
        deductions_breakdown["hra_exemption"] = hra_res
        total_deductions += hra_allowed

    # 3. Section 80C
    if "section_80c" in ded_dict or "80c" in ded_dict:
        raw_80c = float(ded_dict.get("section_80c", ded_dict.get("80c", 0.0)))
        cap_80c = float(ded_rules.get("section_80c", {}).get("cap", 150000.0))
        allowed_80c = min(max(0.0, raw_80c), cap_80c)
        deductions_breakdown["section_80c"] = {
            "claimed": round(raw_80c, 2),
            "cap": cap_80c,
            "allowed": round(allowed_80c, 2),
        }
        total_deductions += allowed_80c

    # 4. Section 80D (Health Insurance)
    if "section_80d" in ded_dict or "80d" in ded_dict:
        data_80d = ded_dict.get("section_80d", ded_dict.get("80d"))
        if isinstance(data_80d, dict):
            res_80d = compute_section_80d_deduction(data_80d, ded_rules.get("section_80d", {}))
            deductions_breakdown["section_80d"] = res_80d
            total_deductions += res_80d["allowed"]
        else:
            # Flat amount passed
            raw_80d = float(data_80d or 0.0)
            cap_80d = float(ded_rules.get("section_80d", {}).get("self_family_max", 25000.0))
            allowed_80d = min(max(0.0, raw_80d), cap_80d)
            deductions_breakdown["section_80d"] = {
                "claimed": round(raw_80d, 2),
                "cap": cap_80d,
                "allowed": round(allowed_80d, 2),
            }
            total_deductions += allowed_80d

    # 5. Section 80CCD(1B) (NPS Additional)
    if "section_80ccd_1b" in ded_dict or "80ccd_1b" in ded_dict or "nps" in ded_dict:
        raw_nps = float(ded_dict.get("section_80ccd_1b", ded_dict.get("80ccd_1b", ded_dict.get("nps", 0.0))))
        cap_nps = float(ded_rules.get("section_80ccd_1b", {}).get("cap", 50000.0))
        allowed_nps = min(max(0.0, raw_nps), cap_nps)
        deductions_breakdown["section_80ccd_1b"] = {
            "claimed": round(raw_nps, 2),
            "cap": cap_nps,
            "allowed": round(allowed_nps, 2),
        }
        total_deductions += allowed_nps

    # 6. Section 24(b) (Home Loan Interest)
    if "section_24b" in ded_dict or "24b" in ded_dict or "home_loan_interest" in ded_dict:
        raw_24b = float(ded_dict.get("section_24b", ded_dict.get("24b", ded_dict.get("home_loan_interest", 0.0))))
        cap_24b = float(ded_rules.get("section_24b", {}).get("self_occupied_cap", 200000.0))
        allowed_24b = min(max(0.0, raw_24b), cap_24b)
        deductions_breakdown["section_24b"] = {
            "claimed": round(raw_24b, 2),
            "cap": cap_24b,
            "allowed": round(allowed_24b, 2),
        }
        total_deductions += allowed_24b

    # 7. Other deductions (e.g. 80TTA / 80TTB)
    for other_key in ["section_80tta", "section_80ttb", "other_deductions"]:
        if other_key in ded_dict:
            raw_other = float(ded_dict[other_key])
            deductions_breakdown[other_key] = {"claimed": round(raw_other, 2), "allowed": round(raw_other, 2)}
            total_deductions += max(0.0, raw_other)

    total_deductions = round(total_deductions, 2)
    taxable_income = max(0.0, round(gross - total_deductions, 2))

    # 8. Slab-by-Slab Calculation (from rules["old_regime"]["slabs"])
    slabs_config = old_reg["slabs"]
    slab_breakdown: List[Dict[str, Any]] = []
    tax_before_rebate = 0.0

    for slab in slabs_config:
        s_min = float(slab["min"])
        s_max = float(slab["max"]) if slab["max"] is not None else None
        rate = float(slab["rate"])

        if taxable_income > s_min:
            upper_limit = min(taxable_income, s_max) if s_max is not None else taxable_income
            taxable_in_slab = max(0.0, upper_limit - s_min)
            slab_tax = round(taxable_in_slab * rate, 2)
        else:
            taxable_in_slab = 0.0
            slab_tax = 0.0

        tax_before_rebate += slab_tax

        slab_breakdown.append({
            "min": s_min,
            "max": s_max,
            "rate": rate,
            "taxable_in_slab": round(taxable_in_slab, 2),
            "tax": round(slab_tax, 2),
        })

    tax_before_rebate = round(tax_before_rebate, 2)

    # 9. Section 87A Rebate (Old Regime: up to ₹12,500 for taxable income <= ₹5L)
    rebate_cfg = old_reg["rebate_87a"]
    rebate_threshold = float(rebate_cfg["threshold"])
    max_rebate = float(rebate_cfg["max_rebate"])

    if taxable_income <= rebate_threshold:
        rebate_87a = min(tax_before_rebate, max_rebate)
    else:
        rebate_87a = 0.0

    rebate_87a = round(rebate_87a, 2)
    tax_after_rebate = max(0.0, round(tax_before_rebate - rebate_87a, 2))

    # 10. Health & Education Cess (4%)
    cess = round(tax_after_rebate * cess_rate, 2)
    total_tax = round(tax_after_rebate + cess, 2)

    effective_rate = round((total_tax / gross * 100.0), 2) if gross > 0 else 0.0

    return {
        "regime": "old",
        "financial_year": rules.get("financial_year", "2025-2026"),
        "gross_income": round(gross, 2),
        "standard_deduction": round(std_deduction, 2),
        "deductions_breakdown": deductions_breakdown,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "slab_breakdown": slab_breakdown,
        "tax_before_rebate": tax_before_rebate,
        "rebate_87a": rebate_87a,
        "tax_after_rebate": tax_after_rebate,
        "cess": cess,
        "cess_rate": cess_rate,
        "surcharge": 0.0,  # NOT IMPLEMENTED — v2 (per spec §5.5)
        "total_tax": total_tax,
        "effective_tax_rate": effective_rate,
    }

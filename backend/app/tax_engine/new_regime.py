"""
New Tax Regime Computation Engine (Task 5.2).

Pure function implementing Section 115BAC tax calculations for FY 2025-26.
Strictly loads all slabs, deductions, 87A rebate, and marginal relief from the rules object.
Contains zero hardcoded tax figures in the function body.
"""

from typing import Any, Dict, List, Optional


def compute_new_regime_tax(
    gross_income: float,
    rules: Dict[str, Any],
    is_salaried: bool = True,
) -> Dict[str, Any]:
    """
    Computes tax liability under the New Tax Regime (Section 115BAC) as a pure function.

    Parameters:
        gross_income: Total gross annual income in INR (float >= 0)
        rules: Parsed tax rules dictionary (e.g. from data/tax_rules/fy_2025_26.json)
        is_salaried: Whether standard deduction for salaried individuals applies

    Returns:
        Structured breakdown of taxable income, slab-by-slab tax, 87A rebate,
        marginal relief, cess, and final net tax liability.
    """
    gross = max(0.0, float(gross_income))
    new_reg = rules["new_regime"]
    cess_rate = float(rules["cess"]["rate"])

    # 1. Standard Deduction (purely from rules config)
    std_deduction_amount = float(new_reg["standard_deduction"]) if is_salaried else 0.0
    taxable_income = max(0.0, gross - std_deduction_amount)

    # 2. Slab-by-Slab Calculation (purely from rules["new_regime"]["slabs"])
    slabs_config = new_reg["slabs"]
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

    # 3. Section 87A Rebate & Marginal Relief (purely from rules config)
    rebate_cfg = new_reg["rebate_87a"]
    rebate_threshold = float(rebate_cfg["threshold"])
    max_rebate = float(rebate_cfg["max_rebate"])
    marginal_relief_cfg = rebate_cfg.get("marginal_relief", {})
    marginal_relief_enabled = marginal_relief_cfg.get("enabled", False)

    rebate_87a = 0.0
    marginal_relief = 0.0

    if taxable_income <= rebate_threshold:
        # Full or partial rebate up to max_rebate
        rebate_87a = min(tax_before_rebate, max_rebate)
        tax_after_rebate = max(0.0, tax_before_rebate - rebate_87a)
    elif marginal_relief_enabled and taxable_income > rebate_threshold:
        # Marginal Relief: Tax payable on income just exceeding ₹12L cannot exceed the excess income
        excess_income = taxable_income - rebate_threshold
        if tax_before_rebate > excess_income:
            marginal_relief = round(tax_before_rebate - excess_income, 2)
            tax_after_rebate = round(excess_income, 2)
        else:
            marginal_relief = 0.0
            tax_after_rebate = tax_before_rebate
    else:
        rebate_87a = 0.0
        marginal_relief = 0.0
        tax_after_rebate = tax_before_rebate

    tax_after_rebate = round(tax_after_rebate, 2)

    # 4. Health & Education Cess (4%)
    cess = round(tax_after_rebate * cess_rate, 2)
    total_tax = round(tax_after_rebate + cess, 2)

    effective_rate = round((total_tax / gross * 100.0), 2) if gross > 0 else 0.0

    return {
        "regime": "new",
        "financial_year": rules.get("financial_year", "2025-2026"),
        "gross_income": round(gross, 2),
        "standard_deduction": round(std_deduction_amount, 2),
        "taxable_income": round(taxable_income, 2),
        "slab_breakdown": slab_breakdown,
        "tax_before_rebate": tax_before_rebate,
        "rebate_87a": round(rebate_87a, 2),
        "marginal_relief": round(marginal_relief, 2),
        "tax_after_rebate": tax_after_rebate,
        "cess": cess,
        "cess_rate": cess_rate,
        "surcharge": 0.0,  # NOT IMPLEMENTED — v2 (per spec §5.5)
        "total_tax": total_tax,
        "effective_tax_rate": effective_rate,
    }

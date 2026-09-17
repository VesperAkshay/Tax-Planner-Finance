"""
Tax Regime Comparator (Task 5.4 & 5.5).

Combines New Regime (Section 115BAC) and Old Regime tax computations to compare
tax liabilities, compute net savings, determine the recommended regime,
and calculate the breakeven deduction threshold.
"""

from typing import Any, Dict, Optional, Union

from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.old_regime import compute_old_regime_tax
from app.tax_engine.rules_loader import load_tax_rules


def compute_breakeven_deductions(
    gross_income: float,
    target_tax: float,
    rules: Dict[str, Any],
    is_salaried: bool = True,
) -> float:
    """
    Computes the total deductions (including standard deduction) required under the Old Regime
    to match the New Regime tax liability (target_tax).
    Uses binary search over possible taxable incomes.
    """
    gross = max(0.0, float(gross_income))
    if target_tax <= 0.0:
        # To get 0 tax in Old Regime, taxable income must be <= 5L (87A rebate)
        old_87a_threshold = float(rules["old_regime"]["rebate_87a"]["threshold"])
        return max(0.0, round(gross - old_87a_threshold, 2))

    low = 0.0
    high = gross
    best_deductions = gross

    for _ in range(60):
        mid = (low + high) / 2.0
        # Check tax on taxable income = mid
        res = compute_old_regime_tax(
            gross_income=mid,
            deductions=None,
            rules=rules,
            is_salaried=False,
        )
        if res["total_tax"] > target_tax:
            high = mid
        else:
            low = mid
            best_deductions = max(0.0, gross - mid)

    return round(best_deductions, 2)


def compare_regimes(
    gross_income: float,
    deductions: Optional[Dict[str, Any]] = None,
    rules: Optional[Dict[str, Any]] = None,
    is_salaried: bool = True,
) -> Dict[str, Any]:
    """
    Compares New vs Old Tax Regimes for FY 2025-26 (Tasks 5.4 & 5.5).

    Parameters:
        gross_income: Total gross annual income in INR
        deductions: Dictionary of itemized deductions (80C, 80D, 80CCD, 24b, HRA, etc.)
        rules: Optional parsed tax rules (loads from default JSON if omitted)
        is_salaried: Whether standard deduction applies

    Returns:
        {
            "old": {...},
            "new": {...},
            "recommended": "new" | "old" | "either",
            "savings": float,
            "breakeven_deductions": float,
            "summary": str
        }
    """
    rules_cfg = rules or load_tax_rules()
    gross = max(0.0, float(gross_income))

    # 1. Compute New Regime Tax (Section 115BAC)
    new_result = compute_new_regime_tax(
        gross_income=gross,
        rules=rules_cfg,
        is_salaried=is_salaried,
        deductions=deductions,
    )

    # 2. Compute Old Regime Tax
    old_result = compute_old_regime_tax(
        gross_income=gross,
        deductions=deductions,
        rules=rules_cfg,
        is_salaried=is_salaried,
    )

    # 3. Determine Recommended Regime and Savings
    new_tax = new_result["total_tax"]
    old_tax = old_result["total_tax"]

    if new_tax < old_tax:
        recommended = "new"
        savings = round(old_tax - new_tax, 2)
        summary = (
            f"New Regime is recommended. You save ₹{savings:,.2f} in taxes "
            f"(New: ₹{new_tax:,.2f} vs Old: ₹{old_tax:,.2f})."
        )
    elif old_tax < new_tax:
        recommended = "old"
        savings = round(new_tax - old_tax, 2)
        summary = (
            f"Old Regime is recommended. You save ₹{savings:,.2f} in taxes thanks to your deductions "
            f"(Old: ₹{old_tax:,.2f} vs New: ₹{new_tax:,.2f})."
        )
    else:
        # Under Section 115BAC(1A), New Regime is the default regime if taxes are identical
        recommended = "new"
        savings = 0.0
        summary = (
            f"Both regimes yield identical tax liability of ₹{new_tax:,.2f}. "
            "New Regime is the default regime under Section 115BAC."
        )

    # 4. Breakeven Deduction Threshold
    breakeven_deds = compute_breakeven_deductions(
        gross_income=gross,
        target_tax=new_tax,
        rules=rules_cfg,
        is_salaried=is_salaried,
    )

    return {
        "gross_income": round(gross, 2),
        "is_salaried": is_salaried,
        "old": old_result,
        "new": new_result,
        "recommended": recommended,
        "savings": savings,
        "breakeven_deductions": breakeven_deds,
        "summary": summary,
    }

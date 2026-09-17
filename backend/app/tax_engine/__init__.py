"""
Tax Rules Engine (Phase 5).

Deterministic pure functions for Indian Income Tax computation (FY 2025-26).
"""

from app.tax_engine.comparator import (
    compare_regimes,
    compute_breakeven_deductions,
)
from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.old_regime import (
    compute_hra_exemption,
    compute_old_regime_tax,
    compute_section_80d_deduction,
)
from app.tax_engine.real_world_detectors import (
    compute_filing_deadline_countdown,
    compute_year_over_year_comparison_data,
    detect_capital_gains_activity,
    detect_salary_arrears,
    detect_savings_interest,
    get_ais_26as_checklist,
)
from app.tax_engine.rules_loader import (
    DEFAULT_RULES_PATH,
    clear_rules_cache,
    load_tax_rules,
)

__all__ = [
    "DEFAULT_RULES_PATH",
    "clear_rules_cache",
    "compare_regimes",
    "compute_breakeven_deductions",
    "compute_filing_deadline_countdown",
    "compute_hra_exemption",
    "compute_new_regime_tax",
    "compute_old_regime_tax",
    "compute_section_80d_deduction",
    "compute_year_over_year_comparison_data",
    "detect_capital_gains_activity",
    "detect_salary_arrears",
    "detect_savings_interest",
    "get_ais_26as_checklist",
    "load_tax_rules",
]

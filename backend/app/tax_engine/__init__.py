"""
Tax Rules Engine (Phase 5).

Deterministic pure functions for Indian Income Tax computation (FY 2025-26).
"""

from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.rules_loader import (
    DEFAULT_RULES_PATH,
    clear_rules_cache,
    load_tax_rules,
)

__all__ = [
    "DEFAULT_RULES_PATH",
    "clear_rules_cache",
    "compute_new_regime_tax",
    "load_tax_rules",
]

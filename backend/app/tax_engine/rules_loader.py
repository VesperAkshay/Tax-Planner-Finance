"""
Tax Rules Loader (Phase 5).

Loads and caches JSON tax rule configurations from disk without any hardcoded constants.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

DEFAULT_RULES_PATH: Path = Path("data/tax_rules/fy_2025_26.json")
_CACHED_RULES: Optional[Dict[str, Any]] = None


def load_tax_rules(rules_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Loads and validates the tax rules JSON configuration.
    Uses cached rules if already loaded from default path.
    """
    global _CACHED_RULES
    p = Path(rules_path).resolve() if rules_path else DEFAULT_RULES_PATH.resolve()

    if rules_path is None and _CACHED_RULES is not None:
        return _CACHED_RULES

    if not p.exists():
        raise FileNotFoundError(f"Tax rules configuration file not found at: {p}")

    with open(p, "r", encoding="utf-8") as f:
        rules = json.load(f)

    # Basic structural validation
    required_keys = ["financial_year", "new_regime", "old_regime", "cess"]
    for key in required_keys:
        if key not in rules:
            raise ValueError(f"Invalid tax rules configuration: missing key '{key}'")

    if rules_path is None:
        _CACHED_RULES = rules

    return rules


def clear_rules_cache() -> None:
    """Clears cached rules (useful for test isolation)."""
    global _CACHED_RULES
    _CACHED_RULES = None

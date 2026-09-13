"""
Unit tests for Tax Rules JSON Configuration (Task 5.1).

Validates schema, slab structures, deductions, and constants in data/tax_rules/fy_2025_26.json.
"""

import json
from pathlib import Path
import pytest

RULES_FILE = Path("data/tax_rules/fy_2025_26.json")


def test_tax_rules_file_exists_and_parses():
    assert RULES_FILE.exists(), f"Expected tax rules file at {RULES_FILE}"
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["financial_year"] == "2025-2026"
    assert data["assessment_year"] == "2026-2027"
    assert data["cess"]["rate"] == 0.04
    assert "# NOT IMPLEMENTED — v2" in data["surcharge"]["status"]


def test_new_regime_slabs_and_standard_deduction():
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_reg = data["new_regime"]
    assert new_reg["standard_deduction"] == 75000.0
    assert new_reg["rebate_87a"]["threshold"] == 1200000.0
    assert new_reg["rebate_87a"]["max_rebate"] == 60000.0
    assert new_reg["rebate_87a"]["marginal_relief"]["enabled"] is True

    slabs = new_reg["slabs"]
    assert len(slabs) == 7

    expected_slabs = [
        (0.0, 400000.0, 0.0),
        (400000.0, 800000.0, 0.05),
        (800000.0, 1200000.0, 0.10),
        (1200000.0, 1600000.0, 0.15),
        (1600000.0, 2000000.0, 0.20),
        (2000000.0, 2400000.0, 0.25),
        (2400000.0, None, 0.30),
    ]

    for slab, (exp_min, exp_max, exp_rate) in zip(slabs, expected_slabs):
        assert slab["min"] == exp_min
        assert slab["max"] == exp_max
        assert slab["rate"] == exp_rate


def test_old_regime_slabs_and_deductions():
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    old_reg = data["old_regime"]
    assert old_reg["standard_deduction"] == 50000.0
    assert old_reg["rebate_87a"]["threshold"] == 500000.0
    assert old_reg["rebate_87a"]["max_rebate"] == 12500.0

    slabs = old_reg["slabs"]
    assert len(slabs) == 4

    expected_slabs = [
        (0.0, 250000.0, 0.0),
        (250000.0, 500000.0, 0.05),
        (500000.0, 1000000.0, 0.20),
        (1000000.0, None, 0.30),
    ]

    for slab, (exp_min, exp_max, exp_rate) in zip(slabs, expected_slabs):
        assert slab["min"] == exp_min
        assert slab["max"] == exp_max
        assert slab["rate"] == exp_rate

    # Check section caps
    deductions = old_reg["deductions"]
    assert deductions["section_80c"]["cap"] == 150000.0
    assert deductions["section_80d"]["self_family_max"] == 25000.0
    assert deductions["section_80d"]["self_family_senior_max"] == 50000.0
    assert deductions["section_80d"]["parents_max"] == 25000.0
    assert deductions["section_80d"]["parents_senior_max"] == 50000.0
    assert deductions["section_80d"]["max_allowable"] == 100000.0
    assert deductions["section_80ccd_1b"]["cap"] == 50000.0
    assert deductions["section_24b"]["self_occupied_cap"] == 200000.0

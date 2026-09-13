"""
Unit tests for Tax Regime Comparator (Tasks 5.4 & 5.5).

Tests regime comparison, recommendation logic, savings calculation,
breakeven deductions, and 4% Health & Education Cess application.
"""

import pytest

from app.tax_engine.comparator import (
    compare_regimes,
    compute_breakeven_deductions,
)
from app.tax_engine.rules_loader import load_tax_rules


@pytest.fixture(scope="module")
def rules():
    return load_tax_rules()


def test_compare_regimes_new_regime_better_when_no_deductions(rules):
    """
    At ₹15L gross income with zero deductions (standard deduction only):
    New Regime tax is lower than Old Regime tax.
    """
    res = compare_regimes(1500000.0, deductions=None, rules=rules, is_salaried=True)

    assert res["recommended"] == "new"
    assert res["new"]["total_tax"] < res["old"]["total_tax"]
    assert res["savings"] > 0.0
    assert "New Regime is recommended" in res["summary"]
    assert res["breakeven_deductions"] > 0.0


def test_compare_regimes_old_regime_better_with_heavy_deductions(rules):
    """
    At ₹15L gross income with substantial deductions:
    - Standard deduction: ₹50,000
    - Section 80C: ₹1,50,000
    - Section 24b: ₹2,00,000
    - Section 80CCD(1B): ₹50,000
    - Section 10(13A) HRA exemption: ₹2,40,000
    Total deductions: ₹6,90,000.
    Old Regime tax becomes significantly lower than New Regime (Old: ₹77,480 vs New: ₹97,500).
    """
    deductions = {
        "section_80c": 150000.0,
        "section_24b": 200000.0,
        "section_80ccd_1b": 50000.0,
        "hra": {
            "basic_salary": 600000.0,
            "hra_received": 240000.0,
            "rent_paid": 300000.0,
            "is_metro": True,
        },
    }

    res = compare_regimes(1500000.0, deductions=deductions, rules=rules, is_salaried=True)

    assert res["recommended"] == "old"
    assert res["old"]["total_tax"] < res["new"]["total_tax"]
    assert res["savings"] > 0.0
    assert "Old Regime is recommended" in res["summary"]


def test_cess_applied_to_both_regimes(rules):
    """
    Task 5.5: Confirm 4% Health & Education Cess is applied on top of both regime calculations.
    """
    res = compare_regimes(1800000.0, deductions=None, rules=rules, is_salaried=True)

    # Check New Regime cess
    new_tax_before_cess = res["new"]["tax_after_rebate"]
    expected_new_cess = round(new_tax_before_cess * 0.04, 2)
    assert res["new"]["cess"] == expected_new_cess
    assert res["new"]["cess_rate"] == 0.04
    assert res["new"]["total_tax"] == round(new_tax_before_cess + expected_new_cess, 2)

    # Check Old Regime cess
    old_tax_before_cess = res["old"]["tax_after_rebate"]
    expected_old_cess = round(old_tax_before_cess * 0.04, 2)
    assert res["old"]["cess"] == expected_old_cess
    assert res["old"]["cess_rate"] == 0.04
    assert res["old"]["total_tax"] == round(old_tax_before_cess + expected_old_cess, 2)


def test_surcharge_v2_deferred_status(rules):
    """
    Task 5.5: Assert surcharge is explicitly tagged as # NOT IMPLEMENTED — v2.
    """
    assert "# NOT IMPLEMENTED — v2" in rules["surcharge"]["status"]
    res = compare_regimes(2000000.0, rules=rules)
    assert res["new"]["surcharge"] == 0.0
    assert res["old"]["surcharge"] == 0.0


def test_breakeven_deduction_calculation(rules):
    """
    Verifies that if a user claims exactly the breakeven deductions,
    the Old Regime tax equals the New Regime tax.
    """
    gross = 1600000.0
    res = compare_regimes(gross, rules=rules, is_salaried=True)
    breakeven = res["breakeven_deductions"]

    # Deducting breakeven amount (including std deduction)
    simulated_deductions = {
        "other_deductions": max(0.0, breakeven - 50000.0)  # subtract 50k std deduction
    }
    eval_res = compare_regimes(gross, deductions=simulated_deductions, rules=rules, is_salaried=True)

    # Taxes should be within a tiny tolerance (<= ₹50 due to rounding)
    assert abs(eval_res["old"]["total_tax"] - eval_res["new"]["total_tax"]) <= 50.0

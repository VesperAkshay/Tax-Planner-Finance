"""
Unit tests for Old Tax Regime Computation Engine (Task 5.3).

Validates pure function behavior, slab calculation, 87A rebate, standard deduction,
Section 80C, 80D, 80CCD(1B), Section 24b, and Section 10(13A) HRA exemption.
"""

import pytest

from app.tax_engine.old_regime import (
    compute_hra_exemption,
    compute_old_regime_tax,
    compute_section_80d_deduction,
)
from app.tax_engine.rules_loader import load_tax_rules


@pytest.fixture(scope="module")
def rules():
    return load_tax_rules()


def test_pure_function_zero_hardcoding_with_synthetic_rules():
    """
    Asserts that compute_old_regime_tax depends strictly on the provided rules.
    """
    synthetic_rules = {
        "financial_year": "2099-2100",
        "cess": {"rate": 0.05},  # 5% cess
        "old_regime": {
            "standard_deduction": 60000.0,
            "rebate_87a": {"threshold": 400000.0, "max_rebate": 10000.0},
            "slabs": [
                {"min": 0.0, "max": 300000.0, "rate": 0.0},
                {"min": 300000.0, "max": None, "rate": 0.20},
            ],
            "deductions": {
                "section_80c": {"cap": 100000.0},
            },
        },
    }

    # Gross ₹6,60,000, Std Ded ₹60,000, 80C claimed ₹1,50,000 (capped at ₹1,00,000)
    # Taxable = 6,60,000 - 60,000 - 1,00,000 = ₹5,00,000
    # Tax on 5L: 0-3L @ 0% = 0; 3L-5L (2L) @ 20% = 40,000
    # Above 4L -> 87A rebate = 0
    # Cess 5% = ₹2,000 -> Total = ₹42,000
    res = compute_old_regime_tax(
        660000.0,
        deductions={"section_80c": 150000.0},
        rules=synthetic_rules,
        is_salaried=True,
    )
    assert res["taxable_income"] == 500000.0
    assert res["total_deductions"] == 160000.0  # 60k std + 100k capped 80C
    assert res["tax_before_rebate"] == 40000.0
    assert res["cess"] == 2000.0
    assert res["total_tax"] == 42000.0


def test_benchmark_15_lakh_taxable_income(rules):
    """
    Benchmark: ₹15L taxable income under Old Regime -> ₹2,73,000 tax.
    Tax on 15L:
    0-2.5L: 0
    2.5-5L (2.5L @ 5%): 12,500
    5-10L (5L @ 20%): 1,00,000
    10-15L (5L @ 30%): 1,50,000
    Sum before cess: 2,62,500
    Cess (4%): 10,500
    Total: ₹2,73,000
    """
    res = compute_old_regime_tax(1500000.0, deductions=None, rules=rules, is_salaried=False)
    assert res["taxable_income"] == 1500000.0
    assert res["tax_before_rebate"] == 262500.0
    assert res["rebate_87a"] == 0.0
    assert res["cess"] == 10500.0
    assert res["total_tax"] == 273000.0


def test_benchmark_20_lakh_taxable_income(rules):
    """
    Benchmark: ₹20L taxable income under Old Regime -> ₹4,29,000 tax.
    Tax on 20L:
    0-2.5L: 0
    2.5-5L (2.5L @ 5%): 12,500
    5-10L (5L @ 20%): 1,00,000
    10-20L (10L @ 30%): 3,00,000
    Sum before cess: 4,12,500
    Cess (4%): 16,500
    Total: ₹4,29,000
    """
    res = compute_old_regime_tax(2000000.0, deductions=None, rules=rules, is_salaried=False)
    assert res["taxable_income"] == 2000000.0
    assert res["tax_before_rebate"] == 412500.0
    assert res["cess"] == 16500.0
    assert res["total_tax"] == 429000.0


def test_old_regime_87a_rebate_at_5_lakh(rules):
    """
    Taxable income ₹5,00,000 under Old Regime qualifies for Section 87A rebate (up to ₹12,500).
    Tax: (5L - 2.5L) * 5% = ₹12,500.
    Rebate = ₹12,500 -> Net tax = ₹0 (NIL).
    """
    res = compute_old_regime_tax(500000.0, deductions=None, rules=rules, is_salaried=False)
    assert res["taxable_income"] == 500000.0
    assert res["tax_before_rebate"] == 12500.0
    assert res["rebate_87a"] == 12500.0
    assert res["tax_after_rebate"] == 0.0
    assert res["total_tax"] == 0.0


def test_section_80c_capping(rules):
    """
    Section 80C claims above ₹1,50,000 are capped at ₹1,50,000.
    """
    res = compute_old_regime_tax(
        1200000.0,
        deductions={"section_80c": 220000.0},
        rules=rules,
        is_salaried=False,
    )
    bdown = res["deductions_breakdown"]["section_80c"]
    assert bdown["claimed"] == 220000.0
    assert bdown["allowed"] == 150000.0
    assert res["taxable_income"] == 1050000.0  # 12L - 1.5L


def test_section_80d_age_based_deduction(rules):
    """
    Section 80D: Self (<60) ₹25k cap, Senior Parents (>60) ₹50k cap.
    """
    health_data = {
        "self_family_premium": 30000.0,  # capped at 25,000
        "parents_premium": 60000.0,      # capped at 50,000 (senior)
        "is_self_senior": False,
        "are_parents_senior": True,
        "preventive_health_checkup": 5000.0,
    }

    res_80d = compute_section_80d_deduction(health_data, rules["old_regime"]["deductions"]["section_80d"])
    assert res_80d["self_family_allowed"] == 25000.0
    assert res_80d["parents_allowed"] == 50000.0
    assert res_80d["allowed"] == 75000.0


def test_section_24b_and_80ccd(rules):
    """
    Section 24b home loan interest capped at ₹2,00,000.
    Section 80CCD(1B) NPS contribution capped at ₹50,000.
    """
    res = compute_old_regime_tax(
        1500000.0,
        deductions={
            "section_24b": 350000.0,      # Capped at 2,00,000
            "section_80ccd_1b": 75000.0,  # Capped at 50,000
        },
        rules=rules,
        is_salaried=False,
    )
    assert res["deductions_breakdown"]["section_24b"]["allowed"] == 200000.0
    assert res["deductions_breakdown"]["section_80ccd_1b"]["allowed"] == 50000.0
    assert res["total_deductions"] == 250000.0


def test_section_10_13a_hra_exemption():
    """
    HRA Exemption: Minimum of:
    1. Actual HRA received: ₹2,40,000
    2. Rent paid (₹3,00,000) - 10% basic (₹60,000) = ₹2,40,000
    3. 50% basic (metro): ₹3,00,000
    Exemption = ₹2,40,000.
    """
    hra_data = {
        "basic_salary": 600000.0,
        "hra_received": 240000.0,
        "rent_paid": 300000.0,
        "is_metro": True,
    }
    hra_res = compute_hra_exemption(hra_data)
    assert hra_res["exemption"] == 240000.0
    assert hra_res["rent_excess_over_10pct"] == 240000.0
    assert hra_res["salary_percentage_limit"] == 300000.0

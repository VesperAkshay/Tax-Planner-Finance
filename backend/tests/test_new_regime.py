"""
Unit tests for New Tax Regime Computation Engine (Task 5.2).

Validates pure function behavior, slab calculation, 87A rebate, and benchmark reference values.
"""

import pytest

from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.rules_loader import load_tax_rules


@pytest.fixture(scope="module")
def rules():
    return load_tax_rules()


def test_pure_function_zero_hardcoding_with_synthetic_rules():
    """
    Asserts that compute_new_regime_tax is truly a pure function and strictly depends
    on the provided rules object rather than internal constants.
    """
    synthetic_rules = {
        "financial_year": "2099-2100",
        "cess": {"rate": 0.10},  # 10% cess
        "new_regime": {
            "standard_deduction": 100000.0,
            "rebate_87a": {
                "threshold": 500000.0,
                "max_rebate": 25000.0,
                "marginal_relief": {"enabled": False},
            },
            "slabs": [
                {"min": 0.0, "max": 500000.0, "rate": 0.0},
                {"min": 500000.0, "max": None, "rate": 0.50},  # 50% flat above 5L
            ],
        },
    }

    # Gross ₹11,00,000 -> Standard deduction ₹1,00,000 -> Taxable ₹10,00,000
    # Slab: 0-5L: 0, 5L-10L (5L) @ 50% = ₹2,50,000
    # Cess @ 10% = ₹25,000 -> Total = ₹2,75,000
    result = compute_new_regime_tax(1100000.0, synthetic_rules, is_salaried=True)
    assert result["taxable_income"] == 1000000.0
    assert result["tax_before_rebate"] == 250000.0
    assert result["cess"] == 25000.0
    assert result["total_tax"] == 275000.0


def test_benchmark_8_lakh_gross_nil_tax(rules):
    """
    Benchmark 1: ₹8L salaried gross income -> New Regime NIL tax.
    Gross: ₹8,00,000 - Std Ded: ₹75,000 = Taxable: ₹7,25,000.
    Since taxable income <= ₹12,00,000, 87A rebate offsets 100% of tax.
    """
    res = compute_new_regime_tax(800000.0, rules, is_salaried=True)
    assert res["gross_income"] == 800000.0
    assert res["standard_deduction"] == 75000.0
    assert res["taxable_income"] == 725000.0
    assert res["tax_before_rebate"] == 16250.0  # (7.25L - 4L) * 5%
    assert res["rebate_87a"] == 16250.0
    assert res["tax_after_rebate"] == 0.0
    assert res["cess"] == 0.0
    assert res["total_tax"] == 0.0


def test_benchmark_15_lakh_taxable_income(rules):
    """
    Benchmark 2: ₹15L reference taxable income -> New Regime ₹1,09,200.
    Tax on 15L:
    0-4L: 0
    4-8L (4L @ 5%): 20,000
    8-12L (4L @ 10%): 40,000
    12-15L (3L @ 15%): 45,000
    Tax before cess: 1,05,000
    Cess (4%): 4,200
    Total: ₹1,09,200
    """
    res = compute_new_regime_tax(1500000.0, rules, is_salaried=False)
    assert res["taxable_income"] == 1500000.0
    assert res["tax_before_rebate"] == 105000.0
    assert res["rebate_87a"] == 0.0
    assert res["tax_after_rebate"] == 105000.0
    assert res["cess"] == 4200.0
    assert res["total_tax"] == 109200.0


def test_benchmark_20_lakh_taxable_income(rules):
    """
    Benchmark 3: ₹20L reference taxable income -> New Regime ₹2,08,000.
    Tax on 20L:
    0-4L: 0
    4-8L (4L @ 5%): 20,000
    8-12L (4L @ 10%): 40,000
    12-16L (4L @ 15%): 60,000
    16-20L (4L @ 20%): 80,000
    Tax before cess: 2,00,000
    Cess (4%): 8,000
    Total: ₹2,08,000
    """
    res = compute_new_regime_tax(2000000.0, rules, is_salaried=False)
    assert res["taxable_income"] == 2000000.0
    assert res["tax_before_rebate"] == 200000.0
    assert res["cess"] == 8000.0
    assert res["total_tax"] == 208000.0


def test_marginal_relief_just_above_12_lakh(rules):
    """
    Marginal relief under Section 87A:
    At ₹12,10,000 taxable income, calculated tax is ₹61,500.
    Income exceeding ₹12,00,000 is only ₹10,000.
    Marginal relief caps tax before cess at ₹10,000 (relief = ₹51,500).
    Total tax = 10,000 + 4% cess (400) = ₹10,400.
    """
    res = compute_new_regime_tax(1210000.0, rules, is_salaried=False)
    assert res["taxable_income"] == 1210000.0
    assert res["tax_before_rebate"] == 61500.0
    assert res["marginal_relief"] == 51500.0
    assert res["tax_after_rebate"] == 10000.0
    assert res["cess"] == 400.0
    assert res["total_tax"] == 10400.0

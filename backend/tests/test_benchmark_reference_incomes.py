"""
Automated tests reproducing known benchmark reference values (Task 5.6).

Verifies official FY 2025-26 reference values:
- ₹8L Gross Income -> New Regime Nil Tax (₹0)
- ₹15L Reference Income -> New Regime ₹1,09,200 / Old Regime ₹2,73,000
- ₹20L Reference Income -> New Regime ₹2,08,000 / Old Regime ₹4,29,000
"""

import pytest

from app.tax_engine.comparator import compare_regimes
from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.old_regime import compute_old_regime_tax
from app.tax_engine.rules_loader import load_tax_rules


@pytest.fixture(scope="module")
def rules():
    return load_tax_rules()


def test_benchmark_8_lakh_gross_income_nil_tax(rules):
    """
    Task 5.6 Benchmark: ₹8L gross salaried income -> New Regime NIL tax.
    Gross Income: ₹8,00,000
    Standard Deduction: ₹75,000
    Taxable Income: ₹7,25,000
    Slab Tax: (7,25,000 - 4,00,000) * 5% = ₹16,250
    Section 87A Rebate: ₹16,250 (Full offset since taxable income <= ₹12,00,000)
    Tax After Rebate: ₹0
    Cess: ₹0
    Total Tax: ₹0
    """
    res = compute_new_regime_tax(800000.0, rules=rules, is_salaried=True)

    assert res["gross_income"] == 800000.0
    assert res["standard_deduction"] == 75000.0
    assert res["taxable_income"] == 725000.0
    assert res["tax_before_rebate"] == 16250.0
    assert res["rebate_87a"] == 16250.0
    assert res["tax_after_rebate"] == 0.0
    assert res["cess"] == 0.0
    assert res["total_tax"] == 0.0
    assert res["effective_tax_rate"] == 0.0

    # Compare regimes at ₹8L with zero deductions
    comparison = compare_regimes(800000.0, deductions=None, rules=rules, is_salaried=True)
    assert comparison["recommended"] == "new"
    assert comparison["new"]["total_tax"] == 0.0
    # In Old Regime on 8L salaried: 8L - 50k = 7.5L taxable -> Tax: 12.5k + 2.5L*20%(50k) = 62.5k + 4% cess = ₹65,000
    assert comparison["old"]["total_tax"] == 65000.0
    assert comparison["savings"] == 65000.0


def test_benchmark_15_lakh_reference_income_both_regimes(rules):
    """
    Task 5.6 Benchmark: ₹15L reference income:
    - New Regime: ₹1,09,200
    - Old Regime: ₹2,73,000
    """
    # 1. New Regime on ₹15,00,000 reference taxable income (non-salaried / after std ded)
    new_res = compute_new_regime_tax(1500000.0, rules=rules, is_salaried=False)

    assert new_res["taxable_income"] == 1500000.0
    # Slab Breakdown:
    # 0 to 4L @ 0% = ₹0
    # 4L to 8L @ 5% = ₹20,000
    # 8L to 12L @ 10% = ₹40,000
    # 12L to 15L @ 15% = ₹45,000
    # Tax Before Cess = ₹1,05,000
    assert new_res["tax_before_rebate"] == 105000.0
    assert new_res["rebate_87a"] == 0.0
    # 4% Health & Education Cess = 1,05,000 * 0.04 = ₹4,200
    assert new_res["cess"] == 4200.0
    # Total Tax = ₹1,09,200
    assert new_res["total_tax"] == 109200.0

    # 2. Old Regime on ₹15,00,000 reference taxable income
    old_res = compute_old_regime_tax(1500000.0, deductions=None, rules=rules, is_salaried=False)

    assert old_res["taxable_income"] == 1500000.0
    # Slab Breakdown:
    # 0 to 2.5L @ 0% = ₹0
    # 2.5L to 5L @ 5% = ₹12,500
    # 5L to 10L @ 20% = ₹1,00,000
    # 10L to 15L @ 30% = ₹1,50,000
    # Tax Before Cess = ₹2,62,500
    assert old_res["tax_before_rebate"] == 262500.0
    assert old_res["rebate_87a"] == 0.0
    # 4% Health & Education Cess = 2,62,500 * 0.04 = ₹10,500
    assert old_res["cess"] == 10500.0
    # Total Tax = ₹2,73,000
    assert old_res["total_tax"] == 273000.0

    # Comparison validation
    comparison = compare_regimes(1500000.0, deductions=None, rules=rules, is_salaried=False)
    assert comparison["new"]["total_tax"] == 109200.0
    assert comparison["old"]["total_tax"] == 273000.0
    assert comparison["recommended"] == "new"
    assert comparison["savings"] == 163800.0  # 2,73,000 - 1,09,200


def test_benchmark_20_lakh_reference_income_both_regimes(rules):
    """
    Task 5.6 Benchmark: ₹20L reference income:
    - New Regime: ₹2,08,000
    - Old Regime: ₹4,29,000
    """
    # 1. New Regime on ₹20,00,000 reference taxable income
    new_res = compute_new_regime_tax(2000000.0, rules=rules, is_salaried=False)

    assert new_res["taxable_income"] == 2000000.0
    # Slab Breakdown:
    # 0 to 4L @ 0% = ₹0
    # 4L to 8L @ 5% = ₹20,000
    # 8L to 12L @ 10% = ₹40,000
    # 12L to 16L @ 15% = ₹60,000
    # 16L to 20L @ 20% = ₹80,000
    # Tax Before Cess = ₹2,00,000
    assert new_res["tax_before_rebate"] == 200000.0
    assert new_res["rebate_87a"] == 0.0
    # 4% Health & Education Cess = 2,00,000 * 0.04 = ₹8,000
    assert new_res["cess"] == 8000.0
    # Total Tax = ₹2,08,000
    assert new_res["total_tax"] == 208000.0

    # 2. Old Regime on ₹20,00,000 reference taxable income
    old_res = compute_old_regime_tax(2000000.0, deductions=None, rules=rules, is_salaried=False)

    assert old_res["taxable_income"] == 2000000.0
    # Slab Breakdown:
    # 0 to 2.5L @ 0% = ₹0
    # 2.5L to 5L @ 5% = ₹12,500
    # 5L to 10L @ 20% = ₹1,00,000
    # 10L to 20L @ 30% = ₹3,00,000
    # Tax Before Cess = ₹4,12,500
    assert old_res["tax_before_rebate"] == 412500.0
    assert old_res["rebate_87a"] == 0.0
    # 4% Health & Education Cess = 4,12,500 * 0.04 = ₹16,500
    assert old_res["cess"] == 16500.0
    # Total Tax = ₹4,29,000
    assert old_res["total_tax"] == 429000.0

    # Comparison validation
    comparison = compare_regimes(2000000.0, deductions=None, rules=rules, is_salaried=False)
    assert comparison["new"]["total_tax"] == 208000.0
    assert comparison["old"]["total_tax"] == 429000.0
    assert comparison["recommended"] == "new"
    assert comparison["savings"] == 221000.0  # 4,29,000 - 2,08,000


def test_salaried_reference_incomes_with_standard_deduction(rules):
    """
    Tests reference incomes for salaried employees with FY 2025-26 standard deductions
    (₹75,000 New Regime, ₹50,000 Old Regime).
    """
    # ₹15L Salaried Gross
    sal_15l = compare_regimes(1500000.0, deductions=None, rules=rules, is_salaried=True)
    # New Regime: 15L - 75k = 14.25L taxable -> Tax: 20k + 40k + (2.25L * 15% = 33,750) = 93,750 + 4% cess (3,750) = ₹97,500
    assert sal_15l["new"]["standard_deduction"] == 75000.0
    assert sal_15l["new"]["taxable_income"] == 1425000.0
    assert sal_15l["new"]["total_tax"] == 97500.0

    # Old Regime: 15L - 50k = 14.50L taxable -> Tax: 12.5k + 100k + (4.5L * 30% = 1,35,000) = 2,47,500 + 4% cess (9,900) = ₹2,57,400
    assert sal_15l["old"]["standard_deduction"] == 50000.0
    assert sal_15l["old"]["taxable_income"] == 1450000.0
    assert sal_15l["old"]["total_tax"] == 257400.0

    # ₹20L Salaried Gross
    sal_20l = compare_regimes(2000000.0, deductions=None, rules=rules, is_salaried=True)
    # New Regime: 20L - 75k = 19.25L taxable -> Tax: 20k + 40k + 60k + (3.25L * 20% = 65,000) = 1,85,000 + 4% cess (7,400) = ₹1,92,400
    assert sal_20l["new"]["standard_deduction"] == 75000.0
    assert sal_20l["new"]["taxable_income"] == 1925000.0
    assert sal_20l["new"]["total_tax"] == 192400.0

    # Old Regime: 20L - 50k = 19.50L taxable -> Tax: 12.5k + 100k + (9.5L * 30% = 2,85,000) = 3,97,500 + 4% cess (15,900) = ₹4,13,400
    assert sal_20l["old"]["standard_deduction"] == 50000.0
    assert sal_20l["old"]["taxable_income"] == 1950000.0
    assert sal_20l["old"]["total_tax"] == 413400.0

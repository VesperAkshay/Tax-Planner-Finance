"""
Comprehensive Unit Tests for Tax Engine Edge Cases & Marginal Relief (Task 5.7).

Validates:
1. Exact slab boundaries in New Regime (₹4L, ₹8L, ₹12L, ₹16L, ₹20L, ₹24L, and above).
2. Exact slab boundaries in Old Regime (₹2.5L, ₹5L, ₹10L, and above).
3. Section 87A rebate thresholds in both regimes (₹12L in New, ₹5L in Old).
4. Section 87A marginal relief spectrum just above ₹12L taxable income in New Regime.
5. Exact breakeven point where marginal relief phases out in New Regime (~₹12,70,588).
6. Cliff-edge effect in Old Regime above ₹5L (no marginal relief).
7. Extreme/Boundary income inputs: zero, negative, gross < standard deduction, deductions > gross.
8. Flat float 80D deduction vs structured dictionary 80D deduction.
9. HRA exemption edge cases (zero basic, zero rent, zero HRA received).
10. Rules loader error handling (nonexistent file, malformed schema, cache clearing).
"""

import tempfile
from pathlib import Path
import pytest

from app.tax_engine.comparator import compare_regimes, compute_breakeven_deductions
from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.old_regime import (
    compute_hra_exemption,
    compute_old_regime_tax,
    compute_section_80d_deduction,
)
from app.tax_engine.rules_loader import clear_rules_cache, load_tax_rules


@pytest.fixture(scope="module")
def rules():
    return load_tax_rules()


# ==============================================================================
# 1. Exact Slab Boundaries in New Regime (Section 115BAC)
# ==============================================================================


@pytest.mark.parametrize(
    "taxable_income, expected_slab_tax, expected_rebate, expected_relief, expected_tax_after_rebate, expected_cess, expected_total",
    [
        # Boundary 1: ₹4,00,000 (0% slab upper bound)
        (400000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        # Boundary 2: ₹8,00,000 (5% slab upper bound, rebate applies)
        # Tax: (8L - 4L) * 5% = 20,000 -> 87A rebate = 20,000 -> Net 0
        (800000.0, 20000.0, 20000.0, 0.0, 0.0, 0.0, 0.0),
        # Boundary 3: ₹12,00,000 (10% slab upper bound, exact 87A rebate threshold)
        # Tax: 20k + (12L - 8L)*10% = 20k + 40k = 60,000 -> 87A rebate = 60,000 -> Net 0
        (1200000.0, 60000.0, 60000.0, 0.0, 0.0, 0.0, 0.0),
        # Boundary 4: ₹16,00,000 (15% slab upper bound)
        # Tax: 60k + (16L - 12L)*15% = 60k + 60k = 1,20,000; Cess: 4,800 -> Total: 1,24,800
        (1600000.0, 120000.0, 0.0, 0.0, 120000.0, 4800.0, 124800.0),
        # Boundary 5: ₹20,00,000 (20% slab upper bound)
        # Tax: 1.20L + (20L - 16L)*20% = 1.20L + 80k = 2,00,000; Cess: 8,000 -> Total: 2,08,000
        (2000000.0, 200000.0, 0.0, 0.0, 200000.0, 8000.0, 208000.0),
        # Boundary 6: ₹24,00,000 (25% slab upper bound)
        # Tax: 2.00L + (24L - 20L)*25% = 2.00L + 1,00,000 = 3,00,000; Cess: 12,000 -> Total: 3,12,000
        (2400000.0, 300000.0, 0.0, 0.0, 300000.0, 12000.0, 312000.0),
        # Above ₹24,00,000 (30% slab, e.g. ₹25,00,000)
        # Tax: 3.00L + (25L - 24L)*30% = 3.00L + 30,000 = 3,30,000; Cess: 13,200 -> Total: 3,43,200
        (2500000.0, 330000.0, 0.0, 0.0, 330000.0, 13200.0, 343200.0),
    ],
)
def test_new_regime_exact_slab_boundaries(
    rules,
    taxable_income,
    expected_slab_tax,
    expected_rebate,
    expected_relief,
    expected_tax_after_rebate,
    expected_cess,
    expected_total,
):
    res = compute_new_regime_tax(taxable_income, rules, is_salaried=False)
    assert res["taxable_income"] == taxable_income
    assert res["tax_before_rebate"] == expected_slab_tax
    assert res["rebate_87a"] == expected_rebate
    assert res["marginal_relief"] == expected_relief
    assert res["tax_after_rebate"] == expected_tax_after_rebate
    assert res["cess"] == expected_cess
    assert res["total_tax"] == expected_total


# ==============================================================================
# 2. Exact Slab Boundaries in Old Regime
# ==============================================================================


@pytest.mark.parametrize(
    "taxable_income, expected_slab_tax, expected_rebate, expected_tax_after_rebate, expected_cess, expected_total",
    [
        # Boundary 1: ₹2,50,000 (0% slab upper bound)
        (250000.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        # Boundary 2: ₹5,00,000 (5% slab upper bound, exact 87A rebate threshold)
        # Tax: (5L - 2.5L) * 5% = 12,500 -> 87A rebate = 12,500 -> Net 0
        (500000.0, 12500.0, 12500.0, 0.0, 0.0, 0.0),
        # Boundary 3: ₹10,00,000 (20% slab upper bound)
        # Tax: 12.5k + (10L - 5L)*20% = 12.5k + 1,00,000 = 1,12,500; Cess: 4,500 -> Total: 1,17,000
        (1000000.0, 112500.0, 0.0, 112500.0, 4500.0, 117000.0),
        # Above ₹10,00,000 (30% slab, e.g. ₹11,00,000)
        # Tax: 1,12,500 + (11L - 10L)*30% = 1,12,500 + 30,000 = 1,42,500; Cess: 5,700 -> Total: 1,48,200
        (1100000.0, 142500.0, 0.0, 142500.0, 5700.0, 148200.0),
    ],
)
def test_old_regime_exact_slab_boundaries(
    rules,
    taxable_income,
    expected_slab_tax,
    expected_rebate,
    expected_tax_after_rebate,
    expected_cess,
    expected_total,
):
    res = compute_old_regime_tax(taxable_income, deductions=None, rules=rules, is_salaried=False)
    assert res["taxable_income"] == taxable_income
    assert res["tax_before_rebate"] == expected_slab_tax
    assert res["rebate_87a"] == expected_rebate
    assert res["tax_after_rebate"] == expected_tax_after_rebate
    assert res["cess"] == expected_cess
    assert res["total_tax"] == expected_total


# ==============================================================================
# 3. New Regime Section 87A Marginal Relief Spectrum Just Above ₹12L
# ==============================================================================


def test_marginal_relief_at_reversal_point_12_lakh_and_1_rupee(rules):
    """
    Taxable income ₹12,00,001 (1 rupee above threshold).
    Slab tax: 60,000 + (1 * 0.15) = 60,000.15.
    Excess income = ₹1.00.
    Under Section 87A marginal relief, tax payable before cess cannot exceed ₹1.00.
    Marginal relief = 60,000.15 - 1.00 = ₹59,999.15.
    Tax after rebate = ₹1.00.
    Cess = round(1.00 * 0.04, 2) = 0.04.
    Total tax = ₹1.04.
    """
    res = compute_new_regime_tax(1200001.0, rules, is_salaried=False)
    assert res["taxable_income"] == 1200001.0
    assert res["tax_before_rebate"] == 60000.15
    assert res["marginal_relief"] == 59999.15
    assert res["tax_after_rebate"] == 1.0
    assert res["cess"] == 0.04
    assert res["total_tax"] == 1.04


def test_marginal_relief_at_12_lakh_100_rupees(rules):
    """
    Taxable income ₹12,00,100 (₹100 excess).
    Slab tax: 60,000 + 15 = 60,015.
    Excess income: ₹100.
    Marginal relief: 60,015 - 100 = 59,915.
    Tax after relief: ₹100. Cess: ₹4. Total tax: ₹104.
    """
    res = compute_new_regime_tax(1200100.0, rules, is_salaried=False)
    assert res["marginal_relief"] == 59915.0
    assert res["tax_after_rebate"] == 100.0
    assert res["cess"] == 4.0
    assert res["total_tax"] == 104.0


def test_marginal_relief_at_12_lakh_50_thousand(rules):
    """
    Taxable income ₹12,50,000 (₹50,000 excess).
    Slab tax: 60,000 + (50,000 * 0.15) = 67,500.
    Excess income: ₹50,000.
    Marginal relief: 67,500 - 50,000 = 17,500.
    Tax after relief: ₹50,000. Cess (4%): ₹2,000. Total tax: ₹52,000.
    """
    res = compute_new_regime_tax(1250000.0, rules, is_salaried=False)
    assert res["tax_before_rebate"] == 67500.0
    assert res["marginal_relief"] == 17500.0
    assert res["tax_after_rebate"] == 50000.0
    assert res["cess"] == 2000.0
    assert res["total_tax"] == 52000.0


def test_marginal_relief_breakeven_cutoff(rules):
    """
    Breakeven point for marginal relief:
    60,000 + 0.15 * E = E => 0.85 * E = 60,000 => E = 70,588.235...
    - At ₹12,70,588 (E = 70,588):
      Slab tax = 60,000 + (70,588 * 0.15) = 70,588.20 > 70,588.
      Marginal relief of ₹0.20 is granted. Tax = 70,588 + 4% cess (2,823.52) = 73,411.52.
    - At ₹12,70,589 (E = 70,589):
      Slab tax = 60,000 + (70,589 * 0.15) = 70,588.35 <= 70,589.
      No marginal relief is needed (relief = 0.0).
      Tax after relief = 70,588.35. Cess (4%) = 2,823.53. Total = ₹73,411.88.
    """
    res_just_below = compute_new_regime_tax(1270588.0, rules, is_salaried=False)
    assert res_just_below["marginal_relief"] == 0.20
    assert res_just_below["tax_after_rebate"] == 70588.0
    assert res_just_below["cess"] == 2823.52
    assert res_just_below["total_tax"] == 73411.52

    res_just_above = compute_new_regime_tax(1270589.0, rules, is_salaried=False)
    assert res_just_above["marginal_relief"] == 0.0
    assert res_just_above["tax_after_rebate"] == 70588.35
    assert res_just_above["cess"] == 2823.53
    assert res_just_above["total_tax"] == 73411.88


def test_no_marginal_relief_well_above_breakeven(rules):
    """
    Taxable income ₹13,00,000:
    Excess income is ₹1,00,000.
    Slab tax = 60,000 + (1,00,000 * 0.15) = 75,000.
    Since slab tax (75,000) <= excess income (1,00,000), marginal relief is 0.0.
    Cess = 75,000 * 0.04 = 3,000.
    Total = ₹78,000.
    """
    res = compute_new_regime_tax(1300000.0, rules, is_salaried=False)
    assert res["marginal_relief"] == 0.0
    assert res["tax_after_rebate"] == 75000.0
    assert res["cess"] == 3000.0
    assert res["total_tax"] == 78000.0


# ==============================================================================
# 4. Old Regime Cliff-Edge (No Marginal Relief Under Old Regime 87A)
# ==============================================================================


def test_old_regime_cliff_edge_at_5_lakh_1_rupee(rules):
    """
    In Old Regime, Section 87A does NOT have a marginal relief provision.
    At ₹5,00,000 taxable income, tax is ₹0.
    At ₹5,00,001 taxable income, 87A rebate is ₹0.
    Tax: 12,500 + (1 * 0.20) = 12,500.20.
    Cess: round(12,500.20 * 0.04, 2) = 500.01.
    Total: ₹13,000.21.
    """
    res_at_5l = compute_old_regime_tax(500000.0, deductions=None, rules=rules, is_salaried=False)
    assert res_at_5l["total_tax"] == 0.0

    res_cliff = compute_old_regime_tax(500001.0, deductions=None, rules=rules, is_salaried=False)
    assert res_cliff["rebate_87a"] == 0.0
    assert res_cliff["tax_before_rebate"] == 12500.20
    assert res_cliff["cess"] == 500.01
    assert res_cliff["total_tax"] == 13000.21


# ==============================================================================
# 5. Extreme & Boundary Inputs: Zero, Negative, Small Incomes
# ==============================================================================


def test_zero_and_negative_incomes(rules):
    """Zero and negative incomes must be safely clamped to ₹0 tax."""
    res_zero_new = compute_new_regime_tax(0.0, rules, is_salaried=True)
    assert res_zero_new["gross_income"] == 0.0
    assert res_zero_new["taxable_income"] == 0.0
    assert res_zero_new["total_tax"] == 0.0
    assert res_zero_new["effective_tax_rate"] == 0.0

    res_neg_new = compute_new_regime_tax(-50000.0, rules, is_salaried=True)
    assert res_neg_new["gross_income"] == 0.0
    assert res_neg_new["taxable_income"] == 0.0
    assert res_neg_new["total_tax"] == 0.0

    res_zero_old = compute_old_regime_tax(0.0, deductions=None, rules=rules, is_salaried=True)
    assert res_zero_old["gross_income"] == 0.0
    assert res_zero_old["taxable_income"] == 0.0
    assert res_zero_old["total_tax"] == 0.0
    assert res_zero_old["effective_tax_rate"] == 0.0

    res_neg_old = compute_old_regime_tax(-100000.0, deductions=None, rules=rules, is_salaried=True)
    assert res_neg_old["gross_income"] == 0.0
    assert res_neg_old["taxable_income"] == 0.0
    assert res_neg_old["total_tax"] == 0.0


def test_income_less_than_standard_deduction(rules):
    """Gross income less than standard deduction results in ₹0 taxable income."""
    # New regime: gross 50,000 < std ded 75,000
    res_new = compute_new_regime_tax(50000.0, rules, is_salaried=True)
    assert res_new["taxable_income"] == 0.0
    assert res_new["total_tax"] == 0.0

    # Old regime: gross 40,000 < std ded 50,000
    res_old = compute_old_regime_tax(40000.0, deductions=None, rules=rules, is_salaried=True)
    assert res_old["taxable_income"] == 0.0
    assert res_old["total_tax"] == 0.0


def test_deductions_exceeding_gross_income(rules):
    """Total itemized deductions exceeding gross income clamps taxable income to 0."""
    res_old = compute_old_regime_tax(
        300000.0,
        deductions={"section_80c": 150000.0, "section_24b": 200000.0},
        rules=rules,
        is_salaried=True,
    )
    # Gross 3L, std ded 50k + 80C 1.5L + 24b 2L = 4L total deductions
    assert res_old["total_deductions"] == 400000.0
    assert res_old["taxable_income"] == 0.0
    assert res_old["total_tax"] == 0.0


# ==============================================================================
# 6. Flat Float Section 80D & HRA Edge Cases
# ==============================================================================


def test_flat_float_section_80d_deduction(rules):
    """
    Tests when deductions['section_80d'] is provided as a flat float rather than a dict.
    Verifies capping at self_family_max (₹25,000).
    """
    res = compute_old_regime_tax(
        800000.0,
        deductions={"section_80d": 35000.0},  # Flat float exceeds ₹25k cap
        rules=rules,
        is_salaried=False,
    )
    bdown = res["deductions_breakdown"]["section_80d"]
    assert bdown["claimed"] == 35000.0
    assert bdown["cap"] == 25000.0
    assert bdown["allowed"] == 25000.0
    assert res["taxable_income"] == 775000.0


def test_dict_based_section_80d_in_old_regime_tax(rules):
    """
    Tests passing a structured dictionary under 'section_80d' directly to compute_old_regime_tax.
    """
    res = compute_old_regime_tax(
        1000000.0,
        deductions={
            "section_80d": {
                "self_family_premium": 20000.0,
                "parents_premium": 45000.0,
                "are_parents_senior": True,
                "preventive_health_checkup": 5000.0,
            }
        },
        rules=rules,
        is_salaried=False,
    )
    bdown = res["deductions_breakdown"]["section_80d"]
    assert bdown["allowed"] == 70000.0  # 25k self (20k + 5k checkup) + 45k parents = 70k
    assert res["taxable_income"] == 930000.0


def test_section_80g_deduction_in_old_regime(rules):
    """
    Tests Section 80G charitable donations deduction in compute_old_regime_tax.
    """
    res = compute_old_regime_tax(
        1000000.0,
        deductions={"section_80g": 30000.0},
        rules=rules,
        is_salaried=False,
    )
    bdown = res["deductions_breakdown"]["section_80g"]
    assert bdown["claimed"] == 30000.0
    assert bdown["allowed"] == 30000.0
    assert res["taxable_income"] == 970000.0



def test_hra_exemption_zero_cases():
    """HRA exemption when salary, rent, or HRA is zero returns 0 exemption."""
    res_zero_hra = compute_hra_exemption({"basic_salary": 500000.0, "hra_received": 0.0, "rent_paid": 120000.0})
    assert res_zero_hra["exemption"] == 0.0

    res_zero_rent = compute_hra_exemption({"basic_salary": 500000.0, "hra_received": 100000.0, "rent_paid": 0.0})
    assert res_zero_rent["exemption"] == 0.0

    res_zero_basic = compute_hra_exemption({"basic_salary": 0.0, "hra_received": 100000.0, "rent_paid": 120000.0})
    assert res_zero_basic["exemption"] == 0.0


# ==============================================================================
# 7. Comparator Breakeven & Tie Scenarios
# ==============================================================================


def test_comparator_tied_regime_recommends_new(rules):
    """
    When both regimes result in ₹0 tax (e.g. ₹5,00,000 salaried income),
    comparator must recommend 'new' regime as default per Section 115BAC.
    """
    res = compare_regimes(500000.0, deductions=None, rules=rules, is_salaried=True)
    assert res["new"]["total_tax"] == 0.0
    assert res["old"]["total_tax"] == 0.0
    assert res["recommended"] == "new"
    assert res["savings"] == 0.0
    assert "default regime" in res["summary"]


def test_comparator_breakeven_deductions_when_target_tax_is_zero(rules):
    """
    When target tax is 0, breakeven deductions should equal gross minus Old Regime 87A threshold (5L).
    """
    breakeven = compute_breakeven_deductions(800000.0, 0.0, rules, is_salaried=True)
    # Gross 8L - 5L threshold = 3L deductions needed
    assert breakeven == 300000.0


# ==============================================================================
# 8. Rules Loader Error Handling & Cache Clearing
# ==============================================================================


def test_rules_loader_file_not_found():
    """Rules loader raises FileNotFoundError when path does not exist."""
    with pytest.raises(FileNotFoundError):
        load_tax_rules("data/tax_rules/non_existent_rules.json")


def test_rules_loader_invalid_keys(tmp_path):
    """Rules loader raises ValueError when required keys are missing."""
    bad_rules_file = tmp_path / "bad_rules.json"
    bad_rules_file.write_text('{"financial_year": "2025-2026"}', encoding="utf-8")
    with pytest.raises(ValueError, match="missing key"):
        load_tax_rules(bad_rules_file)


def test_rules_loader_cache_clearing():
    """Rules loader clear_rules_cache resets cached instance."""
    rules_1 = load_tax_rules()
    assert rules_1 is not None
    clear_rules_cache()
    rules_2 = load_tax_rules()
    assert rules_2 is not None

"""
Unit tests for the Month-Level Reconciliation Engine (Tasks 4.1 - 4.3).

Verifies month-level matching, dynamic tolerance calculation, and explicit edge case handling
(missing slip, missing credit, bonus/variable pay, and unexplained credit).
"""

from datetime import date
import pytest

from app.reconciliation.constants import (
    DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE,
    FLAG_TYPE_BONUS_VARIABLE_PAY,
    FLAG_TYPE_MISMATCHED_AMOUNT,
    FLAG_TYPE_MISSING_BANK_CREDIT,
    FLAG_TYPE_MISSING_SALARY_SLIP,
    FLAG_TYPE_UNEXPLAINED_CREDIT,
    STATUS_PENDING,
)
from app.reconciliation.matcher import (
    compute_reconciliation_tolerance,
    is_salary_credit_narration,
    reconcile_month,
    reconcile_salary_and_bank,
)
from app.reconciliation.schemas import BankCreditItem, SalarySlipItem


def test_compute_reconciliation_tolerance():
    # Below ₹50,000 net pay: ₹500 is greater than 1%
    assert compute_reconciliation_tolerance(30000.0) == 500.0
    assert compute_reconciliation_tolerance(50000.0) == 500.0

    # Above ₹50,000 net pay: 1% is greater than ₹500
    assert compute_reconciliation_tolerance(80000.0) == 800.0
    assert compute_reconciliation_tolerance(150000.0) == 1500.0


def test_is_salary_credit_narration():
    assert is_salary_credit_narration("ACH/SALARY CREDIT/TECHCORP") is True
    assert is_salary_credit_narration("NEFT-MONTHLY PAYROLL MAY 2025") is True
    assert is_salary_credit_narration("SALARY FOR APRIL") is True
    assert is_salary_credit_narration("UPI-SWIGGY-FOOD") is False
    assert is_salary_credit_narration("ELECTRICITY BILL") is False


def test_month_exact_match(tmp_path):
    slip = SalarySlipItem(month=4, year=2025, net_pay=75000.0, gross_pay=90000.0)
    credit = BankCreditItem(
        date=date(2025, 4, 30),
        amount=75000.0,
        description="SALARY CREDIT APRIL",
        is_salary=True,
    )

    res = reconcile_month(month=4, year=2025, slip=slip, credits=[credit])
    assert res.is_reconciled is True
    assert res.status == "matched"
    assert len(res.flags) == 0


def test_month_match_within_tolerance():
    # Net pay ₹80,000 -> tolerance is ₹800 (1%)
    slip = SalarySlipItem(month=5, year=2025, net_pay=80000.0, gross_pay=95000.0)
    # Credit is ₹80,400 (diff ₹400 <= ₹800 tolerance)
    credit = BankCreditItem(
        date=date(2025, 5, 31),
        amount=80400.0,
        description="SALARY CREDIT MAY",
    )

    res = reconcile_month(month=5, year=2025, slip=slip, credits=[credit])
    assert res.is_reconciled is True
    assert res.status == "matched"
    assert len(res.flags) == 0


def test_month_mismatch_exceeding_tolerance():
    # Net pay ₹80,000 -> tolerance is ₹800 (1%)
    slip = SalarySlipItem(month=5, year=2025, net_pay=80000.0, gross_pay=95000.0)
    # Credit is ₹75,000 (diff ₹5,000 > ₹800 tolerance)
    credit = BankCreditItem(
        date=date(2025, 5, 31),
        amount=75000.0,
        description="SALARY CREDIT MAY",
    )

    res = reconcile_month(month=5, year=2025, slip=slip, credits=[credit])
    assert res.is_reconciled is False
    assert res.status == "mismatched"
    assert len(res.flags) == 1

    flag = res.flags[0]
    assert flag.flag_type == FLAG_TYPE_MISMATCHED_AMOUNT
    assert flag.expected_amount == 80000.0
    assert flag.actual_amount == 75000.0
    assert flag.difference == 5000.0
    assert flag.status == STATUS_PENDING


def test_edge_case_missing_salary_slip():
    # Bank credit exists, but no slip
    credit = BankCreditItem(
        id=99,
        date=date(2025, 6, 30),
        amount=90000.0,
        description="SALARY CREDIT JUNE",
    )

    res = reconcile_month(month=6, year=2025, slip=None, credits=[credit])
    assert res.is_reconciled is False
    assert res.status == "missing_slip"
    assert len(res.flags) == 1
    assert res.flags[0].flag_type == FLAG_TYPE_MISSING_SALARY_SLIP
    assert res.flags[0].actual_amount == 90000.0


def test_edge_case_missing_bank_credit():
    # Slip exists, but zero bank credits
    slip = SalarySlipItem(id=88, month=7, year=2025, net_pay=85000.0, gross_pay=100000.0)

    res = reconcile_month(month=7, year=2025, slip=slip, credits=[])
    assert res.is_reconciled is False
    assert res.status == "missing_credit"
    assert len(res.flags) == 1
    assert res.flags[0].flag_type == FLAG_TYPE_MISSING_BANK_CREDIT
    assert res.flags[0].expected_amount == 85000.0


def test_edge_case_bonus_variable_pay_no_force_average():
    """
    CRITICAL SPEC RULE: 'bonus/variable-pay months (must not be force-matched to an average)'
    When credit significantly exceeds net pay (e.g. bonus), flag as bonus_unmatched without averaging.
    """
    slip = SalarySlipItem(month=3, year=2025, net_pay=80000.0, gross_pay=95000.0)
    # Annual bonus payment of ₹150,000 credited alongside regular salary
    bonus_credit = BankCreditItem(
        date=date(2025, 3, 31),
        amount=150000.0,
        description="ANNUAL PERFORMANCE BONUS + SALARY",
    )

    res = reconcile_month(month=3, year=2025, slip=slip, credits=[bonus_credit])
    assert res.is_reconciled is False
    assert res.status == "bonus_detected"
    assert len(res.flags) == 1

    flag = res.flags[0]
    assert flag.flag_type == FLAG_TYPE_BONUS_VARIABLE_PAY
    assert flag.expected_amount == 80000.0
    assert flag.actual_amount == 150000.0
    assert "Must not be force-averaged" in flag.details


def test_edge_case_extra_unexplained_credit():
    slip = SalarySlipItem(month=10, year=2025, net_pay=70000.0, gross_pay=85000.0)
    regular_credit = BankCreditItem(
        id=1,
        date=date(2025, 10, 31),
        amount=70000.0,
        description="SALARY CREDIT OCT",
    )
    extra_credit = BankCreditItem(
        id=2,
        date=date(2025, 10, 15),
        amount=18000.0,
        description="EXTRA STIPEND / PAYROLL REF 402",
    )

    res = reconcile_month(month=10, year=2025, slip=slip, credits=[regular_credit, extra_credit])
    assert res.is_reconciled is False
    assert len(res.flags) == 1
    assert res.flags[0].flag_type == FLAG_TYPE_UNEXPLAINED_CREDIT
    assert res.flags[0].actual_amount == 18000.0

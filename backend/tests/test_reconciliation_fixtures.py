"""
Automated tests for Reconciliation Fixtures (Tasks 4.5 & 4.6).

Verifies:
- Task 4.5: Fixture test with 3 planted discrepancies (missing month, mismatched amount, extra unexplained credit).
  Confirms all 3 are correctly flagged and nothing else is.
- Task 4.6: Fully-matching fixture test confirming zero false-positive flags.
"""

from datetime import date
import json
from pathlib import Path
import pytest

from app.reconciliation.constants import (
    FLAG_TYPE_MISMATCHED_AMOUNT,
    FLAG_TYPE_MISSING_BANK_CREDIT,
    FLAG_TYPE_UNEXPLAINED_CREDIT,
)
from app.reconciliation.matcher import reconcile_salary_and_bank
from app.reconciliation.schemas import BankCreditItem, SalarySlipItem

FIXTURES_DIR = Path("data/test_fixtures/reconciliation")


def test_task_4_5_planted_discrepancies_fixture():
    """
    Task 4.5 automated test:
    Fixture with 3 planted discrepancies:
    1. Month 7 (July): Missing bank credit.
    2. Month 8 (August): Mismatched amount (₹88,000 vs ₹82,000).
    3. Month 9 (September): Extra unexplained credit (₹25,000 alongside ₹88,000).
    Confirms all 3 are correctly flagged and NOTHING ELSE IS.
    """
    fixture_path = FIXTURES_DIR / "planted_discrepancies.json"
    assert fixture_path.exists(), f"Fixture {fixture_path} must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    slips = [SalarySlipItem(**s) for s in data["salary_slips"]]
    credits = [
        BankCreditItem(
            id=c["id"],
            date=date.fromisoformat(c["date"]),
            amount=c["amount"],
            description=c["description"],
            is_salary=c.get("is_salary", True),
        )
        for c in data["bank_credits"]
    ]

    report = reconcile_salary_and_bank(slips=slips, credits=credits, user_id=10)

    # Confirm exactly 3 flags are produced
    assert len(report.flags) == 3, f"Expected exactly 3 flags, got {len(report.flags)}: {report.flags}"

    flag_types = [f.flag_type for f in report.flags]
    assert FLAG_TYPE_MISSING_BANK_CREDIT in flag_types
    assert FLAG_TYPE_MISMATCHED_AMOUNT in flag_types
    assert FLAG_TYPE_UNEXPLAINED_CREDIT in flag_types

    # 1. Check missing month (July / Month 7)
    july_flag = next(f for f in report.flags if f.month == 7)
    assert july_flag.flag_type == FLAG_TYPE_MISSING_BANK_CREDIT
    assert july_flag.expected_amount == 88000.0

    # 2. Check mismatched amount (August / Month 8)
    aug_flag = next(f for f in report.flags if f.month == 8)
    assert aug_flag.flag_type == FLAG_TYPE_MISMATCHED_AMOUNT
    assert aug_flag.expected_amount == 88000.0
    assert aug_flag.actual_amount == 82000.0
    assert aug_flag.difference == 6000.0

    # 3. Check extra unexplained credit (September / Month 9)
    sep_flag = next(f for f in report.flags if f.month == 9)
    assert sep_flag.flag_type == FLAG_TYPE_UNEXPLAINED_CREDIT
    assert sep_flag.actual_amount == 25000.0


def test_task_4_6_fully_matching_fixture_zero_false_positives():
    """
    Task 4.6 automated test:
    Fully-matching fixture across April, May, and June.
    Confirms ZERO false-positive flags are created.
    """
    fixture_path = FIXTURES_DIR / "fully_matching.json"
    assert fixture_path.exists(), f"Fixture {fixture_path} must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    slips = [SalarySlipItem(**s) for s in data["salary_slips"]]
    credits = [
        BankCreditItem(
            id=c["id"],
            date=date.fromisoformat(c["date"]),
            amount=c["amount"],
            description=c["description"],
            is_salary=c.get("is_salary", True),
        )
        for c in data["bank_credits"]
    ]

    report = reconcile_salary_and_bank(slips=slips, credits=credits, user_id=11)

    # Confirms zero false positives
    assert len(report.flags) == 0, f"Expected 0 flags, got {len(report.flags)}: {report.flags}"
    assert report.matched_months_count == 3
    assert report.flagged_months_count == 0
    assert report.total_flags == 0

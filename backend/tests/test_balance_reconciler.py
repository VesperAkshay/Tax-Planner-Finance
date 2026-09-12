import datetime
from typing import List
import pytest

from app.parsing.balance_reconciler import (
    DEFAULT_BALANCE_TOLERANCE,
    reconcile_statement_balance,
)
from app.parsing.csv_parser import CSVBankParser
from app.parsing.schemas import ParsedTransactionRow, StatementParseResult


def create_mock_row(
    date_str: str,
    amount: float,
    txn_type: str,
    balance: float,
    desc: str = "Test Narration",
) -> ParsedTransactionRow:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return ParsedTransactionRow(
        date=d,
        description=desc,
        amount=amount,
        transaction_type=txn_type,
        balance=balance,
        parse_confidence=0.98,
    )


def test_exact_balance_reconciliation():
    rows = [
        create_mock_row("2024-04-01", 5000.0, "credit", 15000.0),
        create_mock_row("2024-04-05", 2000.0, "debit", 13000.0),
        create_mock_row("2024-04-10", 3500.0, "credit", 16500.0),
    ]
    result = StatementParseResult(
        file_path="mock_stmt.csv",
        file_name="mock_stmt.csv",
        rows=rows,
        opening_balance=10000.0,
        closing_balance=16500.0,
        parse_confidence=0.98,
    )

    reconciled = reconcile_statement_balance(result)
    assert reconciled.balance_reconciled is True
    assert reconciled.parse_status == "completed"
    assert reconciled.needs_review is False
    assert reconciled.balance_discrepancy == 0.0
    assert reconciled.expected_closing_balance == 16500.0
    assert reconciled.total_credits == 8500.0
    assert reconciled.total_debits == 2000.0


def test_balance_reconciliation_within_tolerance():
    # 10000 + 5000 - 2000 = 13000. Stated closing is 13000.50 (diff 0.50 <= 1.0 tolerance)
    rows = [
        create_mock_row("2024-04-01", 5000.0, "credit", 15000.0),
        create_mock_row("2024-04-05", 2000.0, "debit", 13000.0),
    ]
    result = StatementParseResult(
        file_path="mock.csv",
        file_name="mock.csv",
        rows=rows,
        opening_balance=10000.0,
        closing_balance=13000.50,
        parse_confidence=0.95,
    )

    reconciled = reconcile_statement_balance(result, tolerance=1.0)
    assert reconciled.balance_reconciled is True
    assert reconciled.parse_status == "completed"
    assert reconciled.needs_review is False
    assert reconciled.balance_discrepancy == 0.50


def test_balance_reconciliation_mismatch_flags_review():
    # Expected closing = 13000, Stated closing = 14500 (diff 1500)
    rows = [
        create_mock_row("2024-04-01", 5000.0, "credit", 15000.0),
        create_mock_row("2024-04-05", 2000.0, "debit", 13000.0),
    ]
    result = StatementParseResult(
        file_path="mock.csv",
        file_name="mock.csv",
        rows=rows,
        opening_balance=10000.0,
        closing_balance=14500.0,
        parse_confidence=0.95,
    )

    reconciled = reconcile_statement_balance(result)
    assert reconciled.balance_reconciled is False
    assert reconciled.parse_status == "needs_review"
    assert reconciled.needs_review is True
    assert reconciled.balance_discrepancy == 1500.0
    assert reconciled.parse_confidence <= 0.60
    assert any("Balance reconciliation mismatch" in w for w in reconciled.warnings)


def test_running_balance_continuity_mismatch():
    # Row 1 -> Row 2 has an unexpected balance jump
    rows = [
        create_mock_row("2024-04-01", 5000.0, "credit", 15000.0),
        create_mock_row("2024-04-05", 1000.0, "credit", 20000.0),  # expected 16000, got 20000
    ]
    result = StatementParseResult(
        file_path="mock.csv",
        file_name="mock.csv",
        rows=rows,
        opening_balance=10000.0,
        closing_balance=20000.0,
        parse_confidence=0.95,
    )

    reconciled = reconcile_statement_balance(result)
    assert reconciled.balance_reconciled is False
    assert reconciled.needs_review is True
    assert reconciled.parse_status == "needs_review"
    assert any("balance discontinuity" in w for w in reconciled.warnings)


def test_unprovided_closing_balance_inferred():
    rows = [
        create_mock_row("2024-04-01", 1000.0, "debit", 9000.0),
        create_mock_row("2024-04-05", 500.0, "debit", 8500.0),
    ]
    result = StatementParseResult(
        file_path="mock.csv",
        file_name="mock.csv",
        rows=rows,
        opening_balance=10000.0,
        closing_balance=None,
        parse_confidence=0.95,
    )

    reconciled = reconcile_statement_balance(result)
    assert reconciled.balance_reconciled is True
    assert reconciled.closing_balance == 8500.0
    assert reconciled.expected_closing_balance == 8500.0
    assert reconciled.parse_status == "completed"


def test_unprovided_opening_balance_inferred():
    rows = [
        create_mock_row("2024-04-01", 2000.0, "credit", 7000.0),
    ]
    result = StatementParseResult(
        file_path="mock.csv",
        file_name="mock.csv",
        rows=rows,
        opening_balance=None,
        closing_balance=7000.0,
        parse_confidence=0.95,
    )

    reconciled = reconcile_statement_balance(result)
    assert reconciled.balance_reconciled is True
    assert reconciled.opening_balance == 5000.0
    assert reconciled.parse_status == "completed"


def test_empty_statement_fails():
    result = StatementParseResult(
        file_path="empty.csv",
        file_name="empty.csv",
        rows=[],
    )
    reconciled = reconcile_statement_balance(result)
    assert reconciled.parse_status == "failed"
    assert reconciled.balance_reconciled is False
    assert reconciled.needs_review is True
    assert reconciled.parse_confidence == 0.0


def test_to_statement_upload_dict():
    result = StatementParseResult(
        file_path="/path/test.csv",
        file_name="test.csv",
        opening_balance=1000.0,
        closing_balance=2000.0,
        parse_status="completed",
        balance_reconciled=True,
        parse_confidence=0.95,
        total_credits=1000.0,
        total_debits=0.0,
        expected_closing_balance=2000.0,
        balance_discrepancy=0.0,
    )
    d = result.to_statement_upload_dict(user_id=1, account_id=2)
    assert d["user_id"] == 1
    assert d["account_id"] == 2
    assert d["parse_status"] == "completed"
    assert d["balance_reconciled"] is True
    assert d["opening_balance"] == 1000.0
    assert d["closing_balance"] == 2000.0
    assert d["raw_metadata"]["expected_closing_balance"] == 2000.0


def test_csv_parser_with_balance_reconciliation():
    hdfc_csv = """HDFC Bank Statement
Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance
01/04/24,SALARY CREDIT,REF123,01/04/24,,150000.00,150000.00
05/04/24,AMAZON,REF456,05/04/24,5000.00,,145000.00
"""
    parser = CSVBankParser()
    res = parser.parse_content(hdfc_csv, bank_id="hdfc")
    assert res.balance_reconciled is True
    assert res.parse_status == "completed"
    assert res.needs_review is False
    assert res.balance_discrepancy == 0.0
    assert res.closing_balance == 145000.0
    assert res.opening_balance == 0.0
    assert res.total_credits == 150000.0
    assert res.total_debits == 5000.0

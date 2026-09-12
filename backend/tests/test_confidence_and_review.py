import datetime
import pytest

from app.parsing.constants import (
    DEFAULT_REVIEW_THRESHOLD,
    HIGH_CONFIDENCE_ROW_THRESHOLD,
)
from app.parsing.csv_parser import CSVBankParser
from app.parsing.salary_slip_parser import DoclingSalarySlipParser
from app.parsing.schemas import (
    ParsedTransactionRow,
    SalarySlipParseResult,
    StatementParseResult,
)
from app.parsing.balance_reconciler import reconcile_statement_balance


def test_default_review_threshold_is_named_constant():
    """Verify threshold is a named constant and adheres to specifications (Task 2.9)."""
    assert DEFAULT_REVIEW_THRESHOLD == 0.85
    assert HIGH_CONFIDENCE_ROW_THRESHOLD == 0.90
    assert isinstance(DEFAULT_REVIEW_THRESHOLD, float)


def test_row_confidence_auto_flags_review():
    """Verify row-level auto-flagging based on DEFAULT_REVIEW_THRESHOLD."""
    d = datetime.date(2024, 4, 1)

    # High confidence row
    row_high = ParsedTransactionRow(
        date=d,
        description="Amazon Purchase",
        amount=1200.0,
        transaction_type="debit",
        parse_confidence=0.95,
    )
    assert row_high.parse_confidence >= DEFAULT_REVIEW_THRESHOLD
    assert row_high.needs_review is False

    # Low confidence row below threshold
    row_low = ParsedTransactionRow(
        date=d,
        description="Fuzzy narration",
        amount=500.0,
        transaction_type="debit",
        parse_confidence=0.75,
    )
    assert row_low.parse_confidence < DEFAULT_REVIEW_THRESHOLD
    assert row_low.needs_review is True

    # Exactly at boundary
    row_boundary = ParsedTransactionRow(
        date=d,
        description="Boundary test",
        amount=100.0,
        transaction_type="credit",
        parse_confidence=DEFAULT_REVIEW_THRESHOLD,
    )
    assert row_boundary.needs_review is False


def test_row_to_transaction_dict_preserves_review_flag():
    d = datetime.date(2024, 4, 1)
    row_low = ParsedTransactionRow(
        date=d,
        description="Low confidence row",
        amount=500.0,
        transaction_type="debit",
        parse_confidence=0.80,
    )
    tx_dict = row_low.to_transaction_dict(account_id=1, upload_id=2)
    assert tx_dict["needs_review"] is True
    assert tx_dict["parse_confidence"] == 0.80
    assert tx_dict["account_id"] == 1


def test_statement_parse_result_review_threshold_boundary():
    d = datetime.date(2024, 4, 1)
    row1 = ParsedTransactionRow(
        date=d,
        description="Salary",
        amount=50000.0,
        transaction_type="credit",
        balance=50000.0,
        parse_confidence=0.86,
    )

    # Statement with confidence 0.86 >= 0.85
    stmt_above = StatementParseResult(
        file_path="stmt_above.csv",
        file_name="stmt_above.csv",
        rows=[row1],
        opening_balance=0.0,
        closing_balance=50000.0,
        parse_confidence=0.86,
    )
    res_above = reconcile_statement_balance(stmt_above)
    assert res_above.parse_confidence >= DEFAULT_REVIEW_THRESHOLD
    assert res_above.needs_review is False
    assert res_above.parse_status == "completed"

    # Statement with confidence 0.82 < 0.85
    row2 = ParsedTransactionRow(
        date=d,
        description="Salary",
        amount=50000.0,
        transaction_type="credit",
        balance=50000.0,
        parse_confidence=0.82,
    )
    stmt_below = StatementParseResult(
        file_path="stmt_below.csv",
        file_name="stmt_below.csv",
        rows=[row2],
        opening_balance=0.0,
        closing_balance=50000.0,
        parse_confidence=0.82,
    )
    res_below = reconcile_statement_balance(stmt_below)
    assert res_below.parse_confidence < DEFAULT_REVIEW_THRESHOLD
    assert res_below.needs_review is True
    assert res_below.parse_status == "needs_review"


def test_salary_slip_extraction_confidence_scoring():
    parser = DoclingSalarySlipParser(ocr_mode=False)

    # Incomplete slip missing basic and gross pay
    res_incomplete = parser.extract_from_data(
        tables=[],
        markdown_text="Unknown Document",
    )
    assert res_incomplete.extraction_confidence < DEFAULT_REVIEW_THRESHOLD
    assert res_incomplete.needs_review is True

    # Complete slip with valid gross pay
    import pandas as pd
    df_complete = pd.DataFrame({
        "Earnings": ["Basic", "HRA", "Gross Pay"],
        "Amount1": [50000, 20000, 70000],
        "Deductions": ["PF", "Total Deductions", "Net Pay"],
        "Amount2": [6000, 6000, 64000],
    })
    res_complete = parser.extract_from_data(
        tables=[df_complete],
        markdown_text="Payslip for the month of April 2024",
    )
    assert res_complete.extraction_confidence >= DEFAULT_REVIEW_THRESHOLD
    assert res_complete.needs_review is False


def test_csv_parser_confidence_penalization_for_missing_data():
    parser = CSVBankParser()
    # CSV with missing narration and missing running balance
    csv_degraded = """HDFC Bank Statement
Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance
01/04/24,,REF123,01/04/24,,15000.00,
"""
    res = parser.parse_content(csv_degraded, bank_id="hdfc")
    # Row confidence was penalized for missing narration and missing balance
    assert res.rows[0].parse_confidence < 0.90
    assert res.rows[0].description == "Unknown Narration"

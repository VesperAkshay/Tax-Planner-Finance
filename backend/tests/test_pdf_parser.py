from datetime import date
from pathlib import Path
import pytest

from app.parsing.constants import DEFAULT_REVIEW_THRESHOLD
from app.parsing.pdf_parser import DoclingPDFParser, parse_date, parse_numeric
from app.parsing.schemas import ParsedTransactionRow, StatementParseResult


def test_parse_date_formats():
    """Verify parse_date correctly handles Indian and standard bank statement formats."""
    assert parse_date("01/04/2025") == date(2025, 4, 1)
    assert parse_date("15-05-2025") == date(2025, 5, 15)
    assert parse_date("2025-06-30") == date(2025, 6, 30)
    assert parse_date(" 10/12/25 ") == date(2025, 12, 10)
    assert parse_date("invalid-date") is None
    assert parse_date(None) is None


def test_parse_numeric_formats():
    """Verify parse_numeric correctly handles Indian Rupee formatting, commas, signs."""
    assert parse_numeric("1,50,000.00") == 150000.0
    assert parse_numeric("₹ 25,000.50") == 25000.50
    assert parse_numeric("450.00Dr") == 450.0
    assert parse_numeric("(1,200.00)") == -1200.0
    assert parse_numeric("-") is None
    assert parse_numeric("N/A") is None
    assert parse_numeric(None) is None


def test_docling_pdf_parser_on_text_statement():
    """Task 2.1: End-to-end test of DoclingPDFParser on text-based bank statement PDF."""
    fixture_path = Path("data/test_fixtures/sample_hdfc_statement.pdf")
    assert fixture_path.exists(), "Test fixture PDF must exist"

    parser = DoclingPDFParser(ocr_mode="never")
    result = parser.parse(fixture_path)

    assert isinstance(result, StatementParseResult)
    assert result.file_name == "sample_hdfc_statement.pdf"
    assert result.is_scanned is False
    assert result.raw_tables_count >= 1
    assert len(result.rows) == 6

    # Verify structured list of raw rows contains date, description, amount, balance
    first_row = result.rows[0]
    assert isinstance(first_row, ParsedTransactionRow)
    assert first_row.date == date(2025, 4, 1)
    assert "SALARY CREDIT" in first_row.description
    assert first_row.amount == 85000.0
    assert first_row.transaction_type == "credit"
    assert first_row.balance == 115000.0
    assert first_row.parse_confidence >= DEFAULT_REVIEW_THRESHOLD

    # Verify totals and confidence
    assert result.total_credits == 86200.0
    assert result.total_debits == 31049.0
    assert result.parse_confidence >= DEFAULT_REVIEW_THRESHOLD
    assert result.needs_review is False
    assert result.statement_start_date == date(2025, 4, 1)
    assert result.statement_end_date == date(2025, 4, 20)


def test_docling_pdf_parser_on_scanned_statement():
    """Task 2.2: End-to-end test of DoclingPDFParser using OCR on scanned/image bank statement PDF."""
    fixture_path = Path("data/test_fixtures/scanned_hdfc_statement.pdf")
    assert fixture_path.exists(), "Scanned test fixture PDF must exist"

    parser = DoclingPDFParser(ocr_mode="force_ocr")
    result = parser.parse(fixture_path)

    assert isinstance(result, StatementParseResult)
    assert result.file_name == "scanned_hdfc_statement.pdf"
    assert result.is_scanned is True
    assert result.file_type == "pdf_scanned"
    assert len(result.rows) == 6

    # Confirm it returns the EXACT SAME structured row format as text-based (Task 2.2 requirement)
    for row in result.rows:
        assert isinstance(row, ParsedTransactionRow)
        assert isinstance(row.date, date)
        assert isinstance(row.description, str) and len(row.description) > 0
        assert isinstance(row.amount, float) and row.amount > 0
        assert row.transaction_type in ("credit", "debit")

    assert result.total_credits == 86200.0
    assert result.total_debits == 31049.0

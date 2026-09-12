from datetime import date
import pytest
from sqlmodel import SQLModel

from app.models.statement_upload import StatementUpload, StatementUploadCreate
from app.models.transaction import Transaction, TransactionCreate


def test_tables_in_metadata():
    """Ensure statement_uploads and transactions tables are registered."""
    assert "statement_uploads" in SQLModel.metadata.tables
    assert "transactions" in SQLModel.metadata.tables


def test_statement_upload_required_fields():
    """Verify StatementUpload fields per Task 1.2."""
    upload = StatementUpload(
        user_id=10,
        file_name="statement_april_2026.pdf",
        file_path="/data/statements/april.pdf",
        parse_confidence=0.95,
        parse_status="completed",
        balance_reconciled=True,
        opening_balance=10000.0,
        closing_balance=15000.0,
        statement_start_date=date(2026, 4, 1),
        statement_end_date=date(2026, 4, 30),
        needs_review=False,
    )
    assert upload.user_id == 10
    assert upload.parse_confidence == 0.95
    assert upload.parse_status == "completed"
    assert upload.balance_reconciled is True
    assert upload.needs_review is False
    assert upload.statement_start_date == date(2026, 4, 1)


def test_transaction_required_fields():
    """Verify Transaction has all six Task 1.2 required fields."""
    tx = Transaction(
        account_id=1,
        upload_id=5,
        date=date(2026, 4, 15),
        description="UPI/ZOMATO/ORDER987",
        amount=620.0,
        transaction_type="debit",
        balance=45000.0,
        parse_confidence=0.99,
        parse_status="parsed",
        balance_reconciled=True,
        category_confidence=0.95,
        is_self_transfer=False,
        needs_review=False,
    )
    # Check the 6 required fields explicitly
    assert hasattr(tx, "parse_confidence") and tx.parse_confidence == 0.99
    assert hasattr(tx, "parse_status") and tx.parse_status == "parsed"
    assert hasattr(tx, "balance_reconciled") and tx.balance_reconciled is True
    assert hasattr(tx, "category_confidence") and tx.category_confidence == 0.95
    assert hasattr(tx, "is_self_transfer") and tx.is_self_transfer is False
    assert hasattr(tx, "needs_review") and tx.needs_review is False

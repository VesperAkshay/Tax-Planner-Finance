import pytest
from pydantic import ValidationError
from sqlmodel import SQLModel

from app.models.account import Account, AccountCreate
from app.models.user import User, UserCreate


def test_user_and_account_metadata():
    """Verify tables are registered in SQLModel metadata."""
    assert "users" in SQLModel.metadata.tables
    assert "accounts" in SQLModel.metadata.tables


def test_user_model_instantiation():
    """Verify User can be instantiated and defaults are set."""
    user = User(
        email="user@example.com",
        hashed_password="hashed_pw_string",
        full_name="Akshay Sharma",
        pan="ABCDE1234F",
    )
    assert user.email == "user@example.com"
    assert user.full_name == "Akshay Sharma"
    assert user.pan == "ABCDE1234F"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


def test_account_model_instantiation():
    """Verify Account can be instantiated and linked to user_id."""
    account = Account(
        user_id=1,
        account_name="Primary Savings",
        bank_name="HDFC",
        account_number_mask="XXXX5678",
        account_type="savings",
        current_balance=25000.50,
    )
    assert account.user_id == 1
    assert account.account_name == "Primary Savings"
    assert account.bank_name == "HDFC"
    assert account.currency == "INR"
    assert account.current_balance == 25000.50


def test_user_create_validation():
    """Verify password length constraints on UserCreate."""
    with pytest.raises(ValidationError):
        UserCreate(email="invalid@example.com", password="123")  # too short (< 8 chars)

    valid = UserCreate(email="valid@example.com", password="strongpassword123")
    assert valid.email == "valid@example.com"

import pytest
from pydantic import ValidationError

from app.parsing.csv_adapter_schema import BankAdapterConfig, SignConvention


def test_valid_separate_columns_adapter():
    """Verify adapter config with separate debit and credit columns."""
    config = BankAdapterConfig(
        bank_id="hdfc_bank",
        bank_name="HDFC Bank",
        description="Standard HDFC Retail NetBanking CSV",
        skip_rows=1,
        header_signatures=["Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt."],
        date_column="Date",
        date_format="%d/%m/%y",
        alternative_date_formats=["%d/%m/%Y"],
        description_column="Narration",
        reference_column="Chq./Ref.No.",
        balance_column="Closing Balance",
        sign_convention=SignConvention.SEPARATE_COLUMNS,
        debit_column="Withdrawal Amt.",
        credit_column="Deposit Amt.",
    )
    assert config.bank_id == "hdfc_bank"
    assert config.sign_convention == SignConvention.SEPARATE_COLUMNS
    assert config.debit_column == "Withdrawal Amt."


def test_valid_signed_amount_adapter():
    """Verify adapter config with single signed amount column."""
    config = BankAdapterConfig(
        bank_id="custom_bank",
        bank_name="Custom Bank",
        date_column="TxnDate",
        description_column="Description",
        amount_column="Amount",
        sign_convention=SignConvention.SIGNED_AMOUNT,
        positive_is_credit=True,
    )
    assert config.sign_convention == SignConvention.SIGNED_AMOUNT
    assert config.positive_is_credit is True


def test_valid_type_indicator_adapter():
    """Verify adapter config with amount column and Cr/Dr type indicator column."""
    config = BankAdapterConfig(
        bank_id="sbi_bank",
        bank_name="State Bank of India",
        date_column="Txn Date",
        description_column="Description",
        amount_column="Amount",
        type_column="Type",
        sign_convention=SignConvention.TYPE_INDICATOR,
        type_mapping={"cr": "credit", "dr": "debit"},
    )
    assert config.sign_convention == SignConvention.TYPE_INDICATOR
    assert config.type_column == "Type"


def test_invalid_convention_missing_required_fields():
    """Verify validation error when required convention columns are omitted."""
    # Missing debit and credit columns for SEPARATE_COLUMNS
    with pytest.raises(ValidationError):
        BankAdapterConfig(
            bank_id="bad_bank",
            bank_name="Bad Bank",
            date_column="Date",
            description_column="Narration",
            sign_convention=SignConvention.SEPARATE_COLUMNS,
            # Neither debit_column nor credit_column supplied
        )

    # Missing amount_column for SIGNED_AMOUNT
    with pytest.raises(ValidationError):
        BankAdapterConfig(
            bank_id="bad_bank_2",
            bank_name="Bad Bank 2",
            date_column="Date",
            description_column="Narration",
            sign_convention=SignConvention.SIGNED_AMOUNT,
            # amount_column missing
        )

    # Missing type_column for TYPE_INDICATOR
    with pytest.raises(ValidationError):
        BankAdapterConfig(
            bank_id="bad_bank_3",
            bank_name="Bad Bank 3",
            date_column="Date",
            description_column="Narration",
            amount_column="Amount",
            sign_convention=SignConvention.TYPE_INDICATOR,
            # type_column missing
        )


def test_json_serialization_roundtrip():
    """Verify JSON dumping and reloading of BankAdapterConfig."""
    config = BankAdapterConfig(
        bank_id="icici_bank",
        bank_name="ICICI Bank",
        date_column="Transaction Date",
        description_column="Particulars",
        balance_column="Balance",
        sign_convention=SignConvention.SEPARATE_COLUMNS,
        debit_column="Withdrawal (Dr)",
        credit_column="Deposit (Cr)",
    )
    json_str = config.model_dump_json()
    loaded = BankAdapterConfig.model_validate_json(json_str)
    assert loaded == config

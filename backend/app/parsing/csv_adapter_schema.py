from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class SignConvention(str, Enum):
    SEPARATE_COLUMNS = "separate_columns"  # distinct debit and credit columns
    SIGNED_AMOUNT = "signed_amount"        # single column (+ for credit, - for debit, or configurable)
    TYPE_INDICATOR = "type_indicator"      # amount column + type indicator column (e.g. CR/DR)


class BankAdapterConfig(BaseModel):
    """
    Schema definition for bank CSV export adapter configurations.
    Specifies column mapping, date parsing, and credit/debit conventions per bank.
    """
    bank_id: str = Field(min_length=1, max_length=50, description="Unique slug for the bank adapter")
    bank_name: str = Field(min_length=1, max_length=100, description="Display name of the bank")
    version: str = Field(default="1.0", description="Configuration version")
    description: Optional[str] = None

    # Header and row detection
    skip_rows: int = Field(default=0, ge=0, description="Number of leading metadata rows to skip")
    header_row_identifier: Optional[str] = Field(
        default=None,
        description="String or substring in the CSV line that marks the actual header row",
    )
    header_signatures: List[str] = Field(
        default_factory=list,
        description="List of exact or partial column names expected to auto-sniff this bank format",
    )

    # Core column mappings
    date_column: str = Field(description="Name of column containing transaction date")
    date_format: str = Field(default="%d/%m/%Y", description="Primary strptime date format")
    alternative_date_formats: List[str] = Field(default_factory=list, description="Fallback date formats")

    description_column: str = Field(description="Name of column containing transaction narration/description")
    reference_column: Optional[str] = Field(default=None, description="Name of column containing reference or cheque number")
    balance_column: Optional[str] = Field(default=None, description="Name of column containing running account balance")

    # Sign convention & amount resolution
    sign_convention: SignConvention = Field(
        default=SignConvention.SEPARATE_COLUMNS,
        description="Mechanism used to distinguish debits from credits",
    )

    # For SEPARATE_COLUMNS convention
    debit_column: Optional[str] = Field(default=None, description="Column name for debit / withdrawal amounts")
    credit_column: Optional[str] = Field(default=None, description="Column name for credit / deposit amounts")

    # For SIGNED_AMOUNT convention
    amount_column: Optional[str] = Field(default=None, description="Column name when single amount column is used")
    positive_is_credit: bool = Field(default=True, description="True if positive numbers are credit, negative are debit")

    # For TYPE_INDICATOR convention
    type_column: Optional[str] = Field(default=None, description="Column name indicating Cr/Dr or Credit/Debit")
    type_mapping: Dict[str, str] = Field(
        default_factory=lambda: {"cr": "credit", "dr": "debit", "c": "credit", "d": "debit"},
        description="Mapping of raw type indicator values to 'credit' or 'debit'",
    )

    @model_validator(mode="after")
    def validate_convention_fields(self) -> "BankAdapterConfig":
        """Validate that the necessary fields for the chosen sign_convention are provided."""
        if self.sign_convention == SignConvention.SEPARATE_COLUMNS:
            if not self.debit_column and not self.credit_column:
                raise ValueError("SEPARATE_COLUMNS requires at least one of 'debit_column' or 'credit_column'")
        elif self.sign_convention == SignConvention.SIGNED_AMOUNT:
            if not self.amount_column:
                raise ValueError("SIGNED_AMOUNT convention requires 'amount_column'")
        elif self.sign_convention == SignConvention.TYPE_INDICATOR:
            if not self.amount_column or not self.type_column:
                raise ValueError("TYPE_INDICATOR convention requires both 'amount_column' and 'type_column'")
        return self

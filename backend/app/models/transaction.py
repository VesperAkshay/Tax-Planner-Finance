from datetime import date as dt_date, datetime as dt_datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.category import Category
    from app.models.statement_upload import StatementUpload


class TransactionBase(SQLModel):
    account_id: int = Field(foreign_key="accounts.id", index=True, nullable=False)
    upload_id: Optional[int] = Field(default=None, foreign_key="statement_uploads.id", index=True)
    date: dt_date = Field(index=True, nullable=False)
    description: str = Field(nullable=False, max_length=1000)
    cleaned_description: Optional[str] = Field(default=None, max_length=1000)
    amount: float = Field(nullable=False)
    transaction_type: str = Field(nullable=False, max_length=10)  # credit | debit
    balance: Optional[float] = Field(default=None)
    reference_number: Optional[str] = Field(default=None, index=True, max_length=100)
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)

    # Core required fields per Task 1.2
    parse_confidence: Optional[float] = Field(default=None)
    parse_status: str = Field(default="parsed", max_length=50)  # parsed, flagged, manual
    balance_reconciled: bool = Field(default=False)
    category_confidence: Optional[float] = Field(default=None)
    is_self_transfer: bool = Field(default=False, index=True)
    needs_review: bool = Field(default=False, index=True)


class Transaction(TransactionBase, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    account: Optional["Account"] = Relationship()
    upload: Optional["StatementUpload"] = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship()


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class TransactionUpdate(SQLModel):
    date: Optional[dt_date] = None
    description: Optional[str] = None
    cleaned_description: Optional[str] = None
    amount: Optional[float] = None
    transaction_type: Optional[str] = None
    balance: Optional[float] = None
    reference_number: Optional[str] = None
    category_id: Optional[int] = None
    parse_confidence: Optional[float] = None
    parse_status: Optional[str] = None
    balance_reconciled: Optional[bool] = None
    category_confidence: Optional[float] = None
    is_self_transfer: Optional[bool] = None
    needs_review: Optional[bool] = None

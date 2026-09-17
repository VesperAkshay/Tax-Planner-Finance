from datetime import date as dt_date, datetime as dt_datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.transaction import Transaction
    from app.models.user import User


class StatementUploadBase(SQLModel):
    account_id: Optional[int] = Field(default=None, foreign_key="accounts.id", index=True)
    file_name: str = Field(nullable=False, max_length=255)
    file_path: str = Field(nullable=False, max_length=512)
    file_type: str = Field(default="pdf_text", max_length=50)  # pdf_text, pdf_scanned, csv
    file_hash: Optional[str] = Field(default=None, index=True, max_length=64)
    parse_status: str = Field(default="pending", index=True, max_length=50)  # pending, completed, failed, needs_review
    parse_confidence: Optional[float] = Field(default=None)
    balance_reconciled: bool = Field(default=False)
    opening_balance: Optional[float] = Field(default=None)
    closing_balance: Optional[float] = Field(default=None)
    statement_start_date: Optional[dt_date] = Field(default=None)
    statement_end_date: Optional[dt_date] = Field(default=None)
    date_range_start: Optional[dt_date] = Field(default=None)
    date_range_end: Optional[dt_date] = Field(default=None)
    needs_review: bool = Field(default=False, index=True)
    raw_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class StatementUpload(StatementUploadBase, table=True):
    __tablename__ = "statement_uploads"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship()
    account: Optional["Account"] = Relationship()
    transactions: List["Transaction"] = Relationship(
        back_populates="upload",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StatementUploadCreate(StatementUploadBase):
    user_id: Optional[int] = None


class StatementUploadRead(StatementUploadBase):
    id: int
    user_id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class StatementUploadUpdate(SQLModel):
    parse_status: Optional[str] = None
    parse_confidence: Optional[float] = None
    balance_reconciled: Optional[bool] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    statement_start_date: Optional[dt_date] = None
    statement_end_date: Optional[dt_date] = None
    date_range_start: Optional[dt_date] = None
    date_range_end: Optional[dt_date] = None
    needs_review: Optional[bool] = None
    raw_metadata: Optional[Dict[str, Any]] = None

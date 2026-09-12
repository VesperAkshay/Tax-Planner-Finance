from datetime import datetime as dt_datetime
from typing import TYPE_CHECKING, Optional
from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.salary_slip import SalarySlip
    from app.models.transaction import Transaction
    from app.models.user import User


class ReconciliationFlagBase(SQLModel):
    salary_slip_id: Optional[int] = Field(default=None, foreign_key="salary_slips.id", index=True)
    transaction_id: Optional[int] = Field(default=None, foreign_key="transactions.id", index=True)
    month: int = Field(ge=1, le=12, nullable=False)
    year: int = Field(ge=2000, le=2100, nullable=False)
    flag_type: str = Field(nullable=False, max_length=100)  # mismatched_amount, missing_salary_slip, missing_bank_credit, bonus_unmatched
    expected_amount: Optional[float] = Field(default=None)
    actual_amount: Optional[float] = Field(default=None)
    difference: Optional[float] = Field(default=None)
    status: str = Field(default="pending", index=True, max_length=50)  # pending, resolved, ignored (indexed per Task 1.6)
    user_note: Optional[str] = Field(default=None, max_length=1000)
    resolved_at: Optional[dt_datetime] = Field(default=None)


class ReconciliationFlag(ReconciliationFlagBase, table=True):
    __tablename__ = "reconciliation_flags"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship()
    salary_slip: Optional["SalarySlip"] = Relationship(back_populates="reconciliation_flags")
    transaction: Optional["Transaction"] = Relationship()


class ReconciliationFlagCreate(ReconciliationFlagBase):
    user_id: Optional[int] = None


class ReconciliationFlagRead(ReconciliationFlagBase):
    id: int
    user_id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class ReconciliationFlagResolve(SQLModel):
    status: str = Field(default="resolved")
    user_note: str = Field(min_length=1, max_length=1000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("resolved", "ignored"):
            raise ValueError("status must be 'resolved' or 'ignored'")
        return v

from datetime import datetime as dt_datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.reconciliation_flag import ReconciliationFlag
    from app.models.user import User


class SalarySlipBase(SQLModel):
    file_name: str = Field(nullable=False, max_length=255)
    file_path: str = Field(nullable=False, max_length=512)
    month: int = Field(ge=1, le=12, nullable=False)
    year: int = Field(ge=2000, le=2100, nullable=False)
    financial_year: str = Field(default="2025-2026", max_length=20)

    # Earnings
    basic: float = Field(default=0.0)
    hra: float = Field(default=0.0)
    lta: float = Field(default=0.0)
    special_allowance: float = Field(default=0.0)
    other_allowances: float = Field(default=0.0)
    gross_pay: float = Field(nullable=False)

    # Deductions
    employee_pf: float = Field(default=0.0)
    employer_pf: float = Field(default=0.0)
    professional_tax: float = Field(default=0.0)
    tds: float = Field(default=0.0)
    other_deductions: float = Field(default=0.0)
    total_deductions: float = Field(default=0.0)
    net_pay: float = Field(nullable=False)

    # Validation & Confidence
    extraction_confidence: Optional[float] = Field(default=None)
    is_gross_valid: bool = Field(default=True)
    needs_review: bool = Field(default=False, index=True)
    raw_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class SalarySlip(SalarySlipBase, table=True):
    __tablename__ = "salary_slips"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship()
    reconciliation_flags: List["ReconciliationFlag"] = Relationship(
        back_populates="salary_slip",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class SalarySlipCreate(SalarySlipBase):
    user_id: Optional[int] = None


class SalarySlipRead(SalarySlipBase):
    id: int
    user_id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class SalarySlipUpdate(SQLModel):
    month: Optional[int] = None
    year: Optional[int] = None
    financial_year: Optional[str] = None
    basic: Optional[float] = None
    hra: Optional[float] = None
    lta: Optional[float] = None
    special_allowance: Optional[float] = None
    other_allowances: Optional[float] = None
    gross_pay: Optional[float] = None
    employee_pf: Optional[float] = None
    employer_pf: Optional[float] = None
    professional_tax: Optional[float] = None
    tds: Optional[float] = None
    other_deductions: Optional[float] = None
    total_deductions: Optional[float] = None
    net_pay: Optional[float] = None
    extraction_confidence: Optional[float] = None
    is_gross_valid: Optional[bool] = None
    needs_review: Optional[bool] = None
    raw_metadata: Optional[Dict[str, Any]] = None

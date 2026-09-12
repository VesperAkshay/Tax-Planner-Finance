from datetime import datetime as dt_datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.user import User


class TaxComputationBase(SQLModel):
    financial_year: str = Field(default="2025-2026", index=True, max_length=20)
    gross_income: float = Field(ge=0.0, nullable=False)

    # Old Regime liability breakdown
    old_regime_taxable_income: float = Field(ge=0.0, nullable=False)
    old_regime_tax: float = Field(ge=0.0, nullable=False)
    old_regime_cess: float = Field(ge=0.0, nullable=False)
    old_regime_total_liability: float = Field(ge=0.0, nullable=False)

    # New Regime liability breakdown
    new_regime_taxable_income: float = Field(ge=0.0, nullable=False)
    new_regime_tax: float = Field(ge=0.0, nullable=False)
    new_regime_cess: float = Field(ge=0.0, nullable=False)
    new_regime_total_liability: float = Field(ge=0.0, nullable=False)

    # Recommendation and differential savings
    recommended_regime: str = Field(nullable=False, max_length=20)  # "old" | "new"
    tax_savings: float = Field(ge=0.0, nullable=False)

    # Detailed payloads
    deductions_applied: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    computation_breakdown: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class TaxComputation(TaxComputationBase, table=True):
    __tablename__ = "tax_computations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship()


class TaxComputationCreate(TaxComputationBase):
    user_id: Optional[int] = None


class TaxComputationRead(TaxComputationBase):
    id: int
    user_id: int
    created_at: dt_datetime
    updated_at: dt_datetime

from datetime import datetime as dt_datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.user import User


class DeductionSource(str, Enum):
    agent_elicited = "agent_elicited"
    catalog_self_added = "catalog_self_added"


class DeductionStatus(str, Enum):
    declared = "declared"
    not_applicable = "not_applicable"


class UserDeclaredDeductionBase(SQLModel):
    financial_year: str = Field(default="2025-2026", index=True, max_length=20)
    section: str = Field(index=True, nullable=False, max_length=50)  # e.g. 80C, 80D, 80CCD(1B), 80G, 24b, HRA
    amount: float = Field(default=0.0, ge=0.0, nullable=False)
    source: DeductionSource = Field(default=DeductionSource.agent_elicited)
    status: DeductionStatus = Field(default=DeductionStatus.declared)
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class UserDeclaredDeduction(UserDeclaredDeductionBase, table=True):
    __tablename__ = "user_declared_deductions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship()


class UserDeclaredDeductionCreate(UserDeclaredDeductionBase):
    user_id: Optional[int] = None


class UserDeclaredDeductionRead(UserDeclaredDeductionBase):
    id: int
    user_id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class UserDeclaredDeductionUpdate(SQLModel):
    amount: Optional[float] = None
    source: Optional[DeductionSource] = None
    status: Optional[DeductionStatus] = None
    metadata_json: Optional[Dict[str, Any]] = None

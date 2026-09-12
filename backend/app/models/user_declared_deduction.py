from datetime import datetime as dt_datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.user import User


class UserDeclaredDeductionBase(SQLModel):
    financial_year: str = Field(default="2025-2026", index=True, max_length=20)
    section: str = Field(index=True, nullable=False, max_length=50)  # e.g. 80C, 80D, 80CCD(1B), 80G, 24b, HRA
    amount: float = Field(ge=0.0, nullable=False)
    source: str = Field(default="agent_elicited", max_length=50)  # agent_elicited, manual, auto_derived
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
    source: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

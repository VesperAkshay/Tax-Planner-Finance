from datetime import date as dt_date, datetime as dt_datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.user import User


class TaxpayerProfileBase(SQLModel):
    name: str = Field(nullable=False, max_length=255)
    relationship: str = Field(default="self", max_length=50)  # self, spouse, parent, child, huf, client
    pan: Optional[str] = Field(default=None, index=True, max_length=10)
    dob: Optional[dt_date] = Field(default=None)
    age_category: str = Field(default="general", max_length=50)  # general, senior (60-79), super_senior (80+)
    persona: str = Field(default="salaried", max_length=50)  # salaried, freelancer_44ada, investor, senior_citizen, huf
    is_default: bool = Field(default=False)
    filing_status: str = Field(default="in_progress", max_length=50)  # in_progress, ready, filed


class TaxpayerProfile(TaxpayerProfileBase, table=True):
    __tablename__ = "taxpayer_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationship to user
    user: Optional["User"] = Relationship()


class TaxpayerProfileCreate(TaxpayerProfileBase):
    pass


class TaxpayerProfileRead(TaxpayerProfileBase):
    id: int
    user_id: int
    created_at: dt_datetime
    updated_at: dt_datetime
    statements_count: Optional[int] = 0
    salary_slips_count: Optional[int] = 0
    readiness_score: Optional[int] = 0
    estimated_tax: Optional[float] = None
    recommended_regime: Optional[str] = None


class TaxpayerProfileUpdate(SQLModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    pan: Optional[str] = None
    dob: Optional[dt_date] = None
    age_category: Optional[str] = None
    persona: Optional[str] = None
    filing_status: Optional[str] = None
    is_default: Optional[bool] = None

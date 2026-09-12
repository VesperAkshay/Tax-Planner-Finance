from datetime import datetime as dt_datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.user import User


class AccountBase(SQLModel):
    account_name: str = Field(nullable=False, max_length=100)
    bank_name: str = Field(nullable=False, max_length=100)
    account_number_mask: Optional[str] = Field(default=None, max_length=30)
    account_type: str = Field(default="savings", max_length=50)
    currency: str = Field(default="INR", max_length=10)
    current_balance: Optional[float] = Field(default=0.0)


class Account(AccountBase, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="accounts")


class AccountCreate(AccountBase):
    user_id: Optional[int] = None


class AccountRead(AccountBase):
    id: int
    user_id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class AccountUpdate(SQLModel):
    account_name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number_mask: Optional[str] = None
    account_type: Optional[str] = None
    currency: Optional[str] = None
    current_balance: Optional[float] = None

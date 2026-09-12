from datetime import datetime as dt_datetime
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.account import Account


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, nullable=False, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    pan: Optional[str] = Field(default=None, index=True, max_length=10)
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    accounts: List["Account"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserRead(UserBase):
    id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    pan: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

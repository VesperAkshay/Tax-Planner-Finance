from datetime import datetime as dt_datetime
from typing import Optional
from sqlmodel import Field, SQLModel

from app.models.common import get_utc_now


class CategoryBase(SQLModel):
    name: str = Field(unique=True, index=True, nullable=False, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    is_income: bool = Field(default=False)
    is_system: bool = Field(default=True)


class Category(CategoryBase, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_income: Optional[bool] = None
    is_system: Optional[bool] = None

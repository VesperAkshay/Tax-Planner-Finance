from datetime import datetime as dt_datetime
from typing import Any, Dict, Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.common import get_utc_now


class TaxRuleVersionBase(SQLModel):
    financial_year: str = Field(unique=True, index=True, nullable=False, max_length=20)  # e.g. "2025-2026"
    version_tag: str = Field(default="v1.0", max_length=20)
    is_active: bool = Field(default=True)
    rules: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class TaxRuleVersion(TaxRuleVersionBase, table=True):
    __tablename__ = "tax_rule_versions"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)


class TaxRuleVersionCreate(TaxRuleVersionBase):
    pass


class TaxRuleVersionRead(TaxRuleVersionBase):
    id: int
    created_at: dt_datetime
    updated_at: dt_datetime


class TaxRuleVersionUpdate(SQLModel):
    version_tag: Optional[str] = None
    is_active: Optional[bool] = None
    rules: Optional[Dict[str, Any]] = None

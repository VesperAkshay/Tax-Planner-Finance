import uuid
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class ApplicableRegimes(str, Enum):
    old_only = "old_only"
    both = "both"


class DeductionCatalogBase(SQLModel):
    section_code: str = Field(unique=True, index=True, nullable=False, max_length=50)  # e.g. '80C', '80D', '80CCD(1B)'
    display_name: str = Field(nullable=False, max_length=255)
    description: str = Field(nullable=False)
    applicable_regimes: ApplicableRegimes = Field(default=ApplicableRegimes.old_only)
    cap_type: str = Field(default="fixed", max_length=50)  # fixed, formula, age_based, severity_based, no_cap, etc.
    cap_amount: Optional[float] = Field(default=None)
    cap_formula: Optional[str] = Field(default=None)
    requires_eligibility_check: bool = Field(default=False)


class DeductionCatalog(DeductionCatalogBase, table=True):
    __tablename__ = "deduction_catalog"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class DeductionCatalogCreate(DeductionCatalogBase):
    pass


class DeductionCatalogRead(DeductionCatalogBase):
    id: uuid.UUID


class DeductionCatalogUpdate(SQLModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    applicable_regimes: Optional[ApplicableRegimes] = None
    cap_type: Optional[str] = None
    cap_amount: Optional[float] = None
    cap_formula: Optional[str] = None
    requires_eligibility_check: Optional[bool] = None

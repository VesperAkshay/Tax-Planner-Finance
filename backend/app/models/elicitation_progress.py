from datetime import datetime as dt_datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
import uuid
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.user import User


class ElicitationStateEnum(str, Enum):
    pending = "pending"
    answered = "answered"
    skipped = "skipped"


class ElicitationProgressBase(SQLModel):
    financial_year: str = Field(index=True, nullable=False, max_length=20)
    section_code: str = Field(index=True, nullable=False, max_length=50)
    state: ElicitationStateEnum = Field(default=ElicitationStateEnum.pending)
    skip_reason: Optional[str] = Field(default=None)


class ElicitationProgress(ElicitationProgressBase, table=True):
    __tablename__ = "elicitation_progress"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship()


class ElicitationProgressCreate(ElicitationProgressBase):
    user_id: Optional[int] = None


class ElicitationProgressRead(ElicitationProgressBase):
    id: uuid.UUID
    user_id: int
    updated_at: dt_datetime


class ElicitationProgressUpdate(SQLModel):
    state: Optional[ElicitationStateEnum] = None
    skip_reason: Optional[str] = None
    updated_at: Optional[dt_datetime] = None

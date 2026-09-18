from datetime import datetime as dt_datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import get_utc_now

if TYPE_CHECKING:
    from app.models.user import User


class UserLLMKeyBase(SQLModel):
    provider: str = Field(index=True, nullable=False, max_length=50)  # openrouter, openai, anthropic, gemini, groq, custom
    model_name: str = Field(default="gpt-4o-mini", nullable=False, max_length=120)
    custom_base_url: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)


class UserLLMKey(UserLLMKeyBase, table=True):
    __tablename__ = "user_llm_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    encrypted_key: str = Field(nullable=False)
    created_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)
    updated_at: dt_datetime = Field(default_factory=get_utc_now, nullable=False)

    # Relationships
    user: Optional["User"] = Relationship()


class UserLLMKeyRead(UserLLMKeyBase):
    id: int
    user_id: int
    masked_key: str
    created_at: dt_datetime
    updated_at: dt_datetime


class UserLLMKeyCreate(SQLModel):
    provider: str
    model_name: str
    api_key: str
    custom_base_url: Optional[str] = None

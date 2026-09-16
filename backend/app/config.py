from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine project root directory (where .env is located)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ROOT_ENV = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:password@ep-placeholder.neon.tech/neondb?ssl=require"
    SYNC_DATABASE_URL: Optional[str] = None

    # Application
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Personal Finance + Tax Regime Planner"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # JWT
    SECRET_KEY: str = "change-this-to-a-super-secret-key-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # LLM & OpenRouter
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Storage Paths
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    TAX_RULES_DIR: str = "./data/tax_rules"
    TEST_FIXTURES_DIR: str = "./data/test_fixtures"

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        """Returns database URL formatted with postgresql+asyncpg driver."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url_resolved(self) -> str:
        """Returns database URL formatted with postgresql driver for Alembic / sync operations."""
        if self.SYNC_DATABASE_URL:
            url = self.SYNC_DATABASE_URL
        else:
            url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        # Ensure sslmode parameter is compatible with psycopg2 if ssl=require is used
        if "?ssl=require" in url:
            url = url.replace("?ssl=require", "?sslmode=require")
        elif "&ssl=require" in url:
            url = url.replace("&ssl=require", "&sslmode=require")
        return url


@lru_cache()
def get_settings() -> Settings:
    return Settings()

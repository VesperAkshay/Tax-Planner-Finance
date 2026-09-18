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
    APP_URL: str = "http://localhost:5173"
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
    OPENROUTER_MODEL: str = "inclusionai/ling-3.0-flash-sante:free"

    # Storage Paths
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
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
        import urllib.parse
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        parsed = urllib.parse.urlparse(url)
        if parsed.query:
            query_params = urllib.parse.parse_qs(parsed.query)
            if "sslmode" in query_params:
                ssl_val = query_params.pop("sslmode")[0]
                query_params["ssl"] = ["require" if "require" in ssl_val else ssl_val]
            query_params.pop("channel_binding", None)
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            url = urllib.parse.urlunparse(parsed._replace(query=new_query))
        return url

    @property
    def sync_database_url_resolved(self) -> str:
        """Returns database URL formatted with postgresql driver for Alembic / sync operations."""
        import urllib.parse
        if self.SYNC_DATABASE_URL:
            url = self.SYNC_DATABASE_URL
        else:
            url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        parsed = urllib.parse.urlparse(url)
        if parsed.query:
            query_params = urllib.parse.parse_qs(parsed.query)
            if "ssl" in query_params and "sslmode" not in query_params:
                ssl_val = query_params.pop("ssl")[0]
                query_params["sslmode"] = ["require" if "require" in ssl_val else ssl_val]
            query_params.pop("channel_binding", None)
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            url = urllib.parse.urlunparse(parsed._replace(query=new_query))
        return url


@lru_cache()
def get_settings() -> Settings:
    return Settings()

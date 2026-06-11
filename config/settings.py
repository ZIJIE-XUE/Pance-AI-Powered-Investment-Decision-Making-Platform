"""Application configuration via Pydantic BaseSettings.

Reads from .env file and environment variables.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from .env and environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Anthropic / Claude API ---
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./robo_advisor.db"

    # --- Redis (None = fallback to diskcache) ---
    REDIS_URL: str | None = None

    # --- Cache TTL ---
    CACHE_DEFAULT_TTL_SECONDS: int = 3600
    ADVISOR_CACHE_TTL_SECONDS: int = 86400  # 24 hours

    # --- Report Storage ---
    REPORT_STORAGE: str = "local"  # "local" or "s3"
    REPORT_OUTPUT_DIR: Path = Path("reports_output")

    # --- Simulation Defaults ---
    DEFAULT_NUM_PATHS: int = 10_000
    DEFAULT_RISK_FREE_RATE: float = 0.03

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    @property
    def anthropic_api_key(self) -> str:
        if not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Please configure it in .env"
            )
        return self.ANTHROPIC_API_KEY


# Global settings instance
settings = Settings()

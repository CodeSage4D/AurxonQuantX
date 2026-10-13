"""AURXON Configuration Module.
Provides validated, immutable runtime settings with environment loading and sensitive credential masking.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings for AURXON Investment Intelligence Hub."""

    ENVIRONMENT: str = Field(default="development", description="App environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    HOST: str = Field(default="127.0.0.1", description="FastAPI bind host")
    PORT: int = Field(default=8000, description="FastAPI bind port")
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:1420,tauri://localhost",
        description="Comma-separated CORS allowed origins",
    )

    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///data/aurxon.sqlite",
        description="Database connection URI",
    )

    # API Keys for Cloud Providers (Optional - graceful degradation to deterministic mock)
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GROQ_API_KEY: str = Field(default="", description="Groq API key")

    # Financial Data Providers
    TAVILY_API_KEY: str = Field(default="", description="Tavily Search API key")
    ALPHA_VANTAGE_API_KEY: str = Field(default="", description="AlphaVantage API key")
    FINNHUB_API_KEY: str = Field(default="", description="Finnhub API key")

    # Risk Limits (Hard Controls)
    ENABLE_REAL_TRADING: bool = Field(default=False, description="REAL MONEY TRADING MUST BE DISABLED")
    PAPER_TRADING_INITIAL_CAPITAL: float = Field(default=1000000.0, description="Paper trading initial capital (INR)")
    MAX_POSITION_SIZE_PERCENT: float = Field(default=10.0, description="Max capital in single position")
    MAX_DRAWDOWN_LIMIT_PERCENT: float = Field(default=15.0, description="Max portfolio drawdown before circuit breaker")

    # Phase 5: Authentication & Operational Hardening
    AUTH_SECRET_KEY: str = Field(
        default="aurxon-quantx-dev-secret-key-32bytes-secure-production-ready",
        description="HMAC secret key for signing user authentication tokens",
    )
    AUTH_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="Token validity in minutes (24h)")
    AUTH_ENABLED: bool = Field(default=True, description="Enforce server-side user authentication on protected endpoints")
    RATE_LIMIT_PER_MINUTE: int = Field(default=120, description="Rate limit requests per client IP")
    MAX_REQUEST_SIZE_BYTES: int = Field(default=10485760, description="10MB max request size limit")
    BACKUP_STORAGE_PATH: str = Field(default="data/backups", description="Local backup archive directory")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def is_cloud_llm_available(self) -> bool:
        return bool(self.OPENAI_API_KEY or self.ANTHROPIC_API_KEY or self.GEMINI_API_KEY or self.GROQ_API_KEY)


settings = Settings()

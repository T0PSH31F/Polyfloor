"""Strongly typed application settings.

All secrets are read from file paths, never from env vars directly.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


def _read_secret_file(path: str | None) -> str | None:
    """Read a secret from a file path. Returns None if path is None or file missing."""
    if path is None:
        return None
    p = Path(path)
    if p.exists():
        return p.read_text().strip()
    return None


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    dsn: str = Field(
        default="postgresql://polyfloor@localhost:5432/polyfloor",
        alias="POLYFLOOR_DATABASE_DSN",
        description="PostgreSQL connection string",
    )
    pool_min: int = Field(default=2, alias="POLYFLOOR_DB_POOL_MIN")
    pool_max: int = Field(default=10, alias="POLYFLOOR_DB_POOL_MAX")


class ExtremeRouterSettings(BaseSettings):
    """ExtremeRouter (free-first model gateway) settings."""

    base_url: str = Field(
        default="https://router.extreme.ai/v1",
        alias="POLYFLOOR_EXTREMEROUTER_BASE_URL",
        description="ExtremeRouter OpenAI-compatible base URL",
    )
    api_key_file: str | None = Field(
        default=None,
        alias="POLYFLOOR_EXTREMEROUTER_API_KEY_FILE",
        description="Path to file containing ExtremeRouter API key",
    )
    reasoning_model: str = Field(
        default="best-reasoning",
        alias="POLYFLOOR_EXTREMEROUTER_REASONING_MODEL",
        description="Logical alias for best reasoning model",
    )
    fast_model: str = Field(
        default="best-fast",
        alias="POLYFLOOR_EXTREMEROUTER_FAST_MODEL",
        description="Logical alias for best fast model",
    )
    code_model: str = Field(
        default="best-code",
        alias="POLYFLOOR_EXTREMEROUTER_CODE_MODEL",
        description="Logical alias for best code model",
    )

    _api_key: str | None = None

    def get_api_key(self) -> str | None:
        if self._api_key is None and self.api_key_file:
            self._api_key = _read_secret_file(self.api_key_file)
        return self._api_key


class HermesSettings(BaseSettings):
    """Hermes/Ollama local model settings."""

    base_url: str = Field(
        default="http://127.0.0.1:11434/v1",
        alias="POLYFLOOR_HERMES_BASE_URL",
        description="Hermes/Ollama OpenAI-compatible base URL",
    )
    model: str = Field(
        default="hermes",
        alias="POLYFLOOR_HERMES_MODEL",
        description="Local Hermes model identifier",
    )


class SecuritySettings(BaseSettings):
    """Authentication and authorization settings."""

    api_token_file: str | None = Field(
        default=None,
        alias="POLYFLOOR_API_TOKEN_FILE",
        description="Path to file containing the API bearer token",
    )
    allowed_origins: str = Field(
        default="http://127.0.0.1:5173",
        alias="POLYFLOOR_ALLOWED_ORIGINS",
        description="Comma-separated list of allowed CORS origins",
    )

    _api_token: str | None = None

    def get_api_token(self) -> str | None:
        if self._api_token is None and self.api_token_file:
            self._api_token = _read_secret_file(self.api_token_file)
        return self._api_token


class PolicySettings(BaseSettings):
    """Model routing and spending policy."""

    allow_paid_models: bool = Field(
        default=False,
        alias="POLYFLOOR_ALLOW_PAID_MODELS",
        description="Allow paid model usage globally",
    )
    paid_daily_budget_usd: float = Field(
        default=0.0,
        alias="POLYFLOOR_PAID_DAILY_BUDGET_USD",
        description="Daily budget cap for paid models in USD",
    )


class OutputSettings(BaseSettings):
    """Filesystem output settings."""

    root: str = Field(
        default="/var/lib/polyfloor/floors",
        alias="POLYFLOOR_OUTPUT_ROOT",
        description="Root directory for floor outputs",
    )


class Settings(BaseSettings):
    """Top-level application settings."""

    model_config = {"env_prefix": "POLYFLOOR_", "case_sensitive": False}

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    extreme_router: ExtremeRouterSettings = Field(default_factory=ExtremeRouterSettings)
    hermes: HermesSettings = Field(default_factory=HermesSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    policy: PolicySettings = Field(default_factory=PolicySettings)
    output: OutputSettings = Field(default_factory=OutputSettings)

    host: str = Field(default="127.0.0.1", alias="POLYFLOOR_HOST")
    port: int = Field(default=8001, alias="POLYFLOOR_PORT")
    log_level: str = Field(default="info", alias="POLYFLOOR_LOG_LEVEL")


def get_settings() -> Settings:
    """Create settings from environment."""
    return Settings()

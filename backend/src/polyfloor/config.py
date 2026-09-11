"""Strongly typed application settings.

Secrets are read from file paths, never from env vars directly. The router API
key lives in a file referenced by ``routerApiKeyFile`` so it never appears in
the process environment or logs.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


def _read_secret_file(path: str | None) -> str | None:
    """Read a secret from a file path. Returns None if path is None or missing."""
    if path is None:
        return None
    p = Path(path)
    if p.exists():
        return p.read_text().strip()
    return None


class Settings(BaseSettings):
    """Top-level Polyfloor settings.

    All fields are configurable via ``POLYFLOOR_*`` environment variables (the
    NixOS module writes these from its options). The database defaults to a
    local SQLite file so a fresh ``nix run`` works with zero external services.
    """

    model_config = {"env_prefix": "POLYFLOOR_", "case_sensitive": False}

    host: str = Field(default="127.0.0.1", description="Bind host.")
    port: int = Field(default=8001, description="Bind port.")
    log_level: str = Field(default="info")

    # SQLite by default; override with a postgres DSN for production.
    database_url: str = Field(
        default="sqlite+aiosqlite:///polyfloor.db",
        description="SQLAlchemy async database URL.",
    )

    data_dir: str = Field(
        default="/var/lib/polyfloor",
        description="Root for per-company workspaces and avatars.",
    )

    static_dir: str | None = Field(
        default=None,
        description="Directory of the built frontend SPA to serve (nix run).",
    )

    # --- Model router (OpenAI-compatible) ---
    router_endpoint: str = Field(
        default="http://127.0.0.1:4000/v1",
        description="OpenAI-compatible router base (Kong / Extreme Router / LiteLLM).",
    )
    router_api_key_file: str | None = Field(
        default=None,
        description="Path to a file containing the router API key.",
    )
    default_hr_model: str = Field(
        default="mimo-v2.5-pro",
        description="Default model id for the HR coordinator agent.",
    )

    # --- Security ---
    allowed_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:5173",
        description="Comma-separated CORS origins.",
    )
    # Optional platform-level bearer token. When unset, the API is open in dev.
    api_token_file: str | None = Field(
        default=None,
        description="Path to a file containing a platform bearer token.",
    )

    # --- Policy ---
    default_wip_limit: int = Field(
        default=3,
        description="Default max IN_PROGRESS tasks per team.",
    )

    _router_api_key: str | None = None
    _api_token: str | None = None

    def router_api_key(self) -> str | None:
        if self._router_api_key is None and self.router_api_key_file:
            self._router_api_key = _read_secret_file(self.router_api_key_file)
        return self._router_api_key

    def api_token(self) -> str | None:
        if self._api_token is None and self.api_token_file:
            self._api_token = _read_secret_file(self.api_token_file)
        return self._api_token

    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

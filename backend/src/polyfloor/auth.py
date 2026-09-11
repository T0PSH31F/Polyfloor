"""Authentication and company-context extraction.

For the OSS MVP, access is scoped by ``company_id`` carried via the
``X-Company-Id`` header (or ``?company_id=`` query param). An optional platform
bearer token (``POLYFLOOR_API_TOKEN_FILE``) gates the whole API in production.

Every request resolves to a :class:`CompanyContext`; endpoints that lack one
return 400. See SPEC §4 (Isolation).
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import HTTPException, Query, Request, status

from .config import get_settings
from .db.models import CompanyContext


@dataclass
class Principal:
    """The actor behind a request."""

    actor: str
    company_id: str | None
    is_platform: bool


_security_cache: dict[str, str | None] = {}


def _platform_token() -> str | None:
    settings = get_settings()
    if "token" not in _security_cache:
        _security_cache["token"] = settings.api_token()
    return _security_cache["token"]


def _check_bearer(request: Request) -> None:
    """If a platform token is configured, require a matching bearer token."""
    expected = _platform_token()
    if not expected:
        return  # open in dev
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = auth.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid bearer token")


def company_context(
    request: Request,
    company_id: str | None = Query(default=None, description="Company tenant id"),
) -> CompanyContext:
    """Resolve a mandatory :class:`CompanyContext` from the request.

    Order: query param ``company_id`` -> ``X-Company-Id`` header.
    """
    _check_bearer(request)
    cid = company_id or request.headers.get("X-Company-Id")
    if not cid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "company_id is required (query param or X-Company-Id header)",
        )
    actor = request.headers.get("X-Actor", "user")
    return CompanyContext(cid, actor=actor, trace_id=request.headers.get("X-Trace-Id"))


def principal(request: Request, company_id: str | None = Query(default=None)) -> Principal:
    """Resolve a :class:`Principal` (used by action dispatch)."""
    _check_bearer(request)
    cid = company_id or request.headers.get("X-Company-Id")
    return Principal(
        actor=request.headers.get("X-Actor", "user"), company_id=cid, is_platform=False
    )


# Compatibility shim for any legacy imports.
require_floor_access = None  # type: ignore[assignment]
require_scope = None  # type: ignore[assignment]

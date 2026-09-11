"""Model router — OpenAI-compatible client to ``POLYFLOOR_ROUTER_ENDPOINT``.

- ``GET /api/models`` proxies ``{router}/models`` and groups models into
  ``free | fast | reasoning | frontier``.
- ``PUT /api/agents/{id}/model`` changes an agent's model (company-scoped).
- When the router is unreachable, returns a clearly-marked mock catalog that
  includes ``mimo-v2.5-pro`` if configured.

The catalog is never hardcoded in the UI — the frontend fetches it live.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from ..config import get_settings

logger = structlog.get_logger()


# Heuristic tier classification by model id substring. Real routers expose a
# owned_by / pricing field we prefer; these are fallbacks.
_REASONING_HINTS = ("o1", "o3", "o4", "reasoning", "thinking", "pro", "mimo", "deepseek-r1")
_FRONTIER_HINTS = ("gpt-4", "gpt-5", "claude-3", "claude-4", "opus", "gemini-1.5", "grok")
_FAST_HINTS = ("mini", "flash", "haiku", "fast", "nano", "8b", "7b")


def classify_tier(model_id: str, owned_by: str | None = None) -> str:
    mid = model_id.lower()
    # Fast/small models first so e.g. gpt-4o-mini and gemini-1.5-flash classify
    # as fast rather than frontier.
    if any(h in mid for h in _FAST_HINTS):
        return "fast"
    if any(h in mid for h in _REASONING_HINTS):
        return "reasoning"
    if any(h in mid for h in _FRONTIER_HINTS):
        return "frontier"
    return "free"


def _format_model(raw: dict[str, Any]) -> dict[str, Any]:
    mid = raw.get("id") or raw.get("name") or "unknown"
    owned_by = raw.get("owned_by") or raw.get("owner") or "unknown"
    tier = classify_tier(mid, owned_by)
    context = raw.get("context_length") or raw.get("context") or 8192
    pricing = raw.get("pricing")
    return {
        "id": mid,
        "owned_by": owned_by,
        "tier": tier,
        "context": int(context) if context else 8192,
        "pricing": pricing,
    }


def _mock_catalog(default_hr_model: str) -> dict[str, list[dict[str, Any]]]:
    """A clearly-marked offline catalog used when no router is reachable."""
    models = [
        {"id": "mimo-v2.5-pro", "owned_by": "xiaomi", "context": 131072},
        {"id": "free-fast-1", "owned_by": "mock", "context": 8192},
        {"id": "free-fast-2", "owned_by": "mock", "context": 16384},
        {"id": "reasoning-mock", "owned_by": "mock", "context": 65536},
    ]
    grouped: dict[str, list[dict[str, Any]]] = {
        "free": [],
        "fast": [],
        "reasoning": [],
        "frontier": [],
    }
    for m in models:
        entry = _format_model(m)
        grouped[entry["tier"]].append(entry)
    # Ensure the configured HR model is present and marked reasoning-tier.
    if not any(m["id"] == default_hr_model for grp in grouped.values() for m in grp):
        grouped["reasoning"].append(
            _format_model({"id": default_hr_model, "owned_by": "configured", "context": 131072})
        )
    return grouped


class ModelRouterService:
    """Service that enumerates models from the router and applies agent model changes."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        default_hr_model: str | None = None,
        timeout: float = 3.0,
    ) -> None:
        settings = get_settings()
        self.endpoint = (endpoint or settings.router_endpoint).rstrip("/")
        self.api_key = api_key or settings.router_api_key()
        self.default_hr_model = default_hr_model or settings.default_hr_model
        self.timeout = timeout

    async def list_models(self) -> dict[str, list[dict[str, Any]]]:
        """Proxy ``{router}/models`` and group by tier. Mock on failure."""
        url = f"{self.endpoint}/models"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning(
                "model_router.unreachable",
                endpoint=self.endpoint,
                error=str(exc),
            )
            catalog = _mock_catalog(self.default_hr_model)
            catalog["_source"] = "mock"  # type: ignore[assignment]
            return catalog

        raw_models = data.get("data") if isinstance(data, dict) else data
        grouped: dict[str, list[dict[str, Any]]] = {
            "free": [],
            "fast": [],
            "reasoning": [],
            "frontier": [],
        }
        for raw in raw_models or []:
            entry = _format_model(raw)
            grouped[entry["tier"]].append(entry)
        grouped["_source"] = "live"  # type: ignore[assignment]
        return grouped

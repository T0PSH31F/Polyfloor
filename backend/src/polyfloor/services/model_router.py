"""Model router — resolves logical aliases to model endpoints.

Multi-provider design:
1. Local Hermes/Ollama if specifically selected
2. Primary provider (Kong gateway) with fallback to ExtremeRouter
3. Paid providers only when explicitly enabled globally AND per floor/role
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ModelEndpoint:
    """Resolved model endpoint for an agent call."""

    base_url: str
    model: str
    api_key: Optional[str] = None
    is_paid: bool = False
    fallback_url: Optional[str] = None
    fallback_api_key: Optional[str] = None


class ModelRouter:
    """Routes logical model aliases to concrete endpoints with fallback support."""

    ALIAS_PREFIXES = ("free://", "hermes:", "paid://")

    def __init__(
        self,
        kong_url: str = "http://127.0.0.1:8000/v1",
        kong_api_key: Optional[str] = None,
        extreme_router_url: str = "https://router.extreme.ai/v1",
        extreme_router_api_key: Optional[str] = None,
        hermes_url: str = "http://127.0.0.1:11434/v1",
        hermes_model: str = "hermes",
        reasoning_alias: str = "best-reasoning",
        fast_alias: str = "best-fast",
        code_alias: str = "best-code",
        allow_paid: bool = False,
        request_timeout_seconds: float = 120.0,
    ):
        self.kong_url = kong_url
        self.kong_api_key = kong_api_key
        self.extreme_router_url = extreme_router_url
        self.extreme_router_api_key = extreme_router_api_key
        self.hermes_url = hermes_url
        self.hermes_model = hermes_model
        self.alias_map = {
            "best-reasoning": reasoning_alias,
            "best-fast": fast_alias,
            "best-code": code_alias,
        }
        self.allow_paid = allow_paid
        self.request_timeout_seconds = request_timeout_seconds

    def resolve(self, model_spec: str, floor_paid_allowed: bool = False) -> ModelEndpoint:
        """Resolve a logical model spec to a primary endpoint and fallback endpoint.

        Args:
            model_spec: e.g. "free://best-reasoning", "hermes:llama3", "paid://gpt-4o"
            floor_paid_allowed: whether the floor has opted into paid models

        Returns:
            ModelEndpoint with primary & fallback configuration
        """
        # Hermes / local model
        if model_spec.startswith("hermes:"):
            local_model = model_spec.removeprefix("hermes:")
            return ModelEndpoint(
                base_url=self.hermes_url,
                model=local_model or self.hermes_model,
                api_key=None,
                is_paid=False,
            )

        # Paid model — requires both global and floor opt-in
        if model_spec.startswith("paid://"):
            if not self.allow_paid:
                raise ValueError(f"Paid models are globally disabled. Cannot use '{model_spec}'")
            if not floor_paid_allowed:
                raise ValueError(
                    f"Paid models are not allowed for this floor. Cannot use '{model_spec}'"
                )
            actual_model = model_spec.removeprefix("paid://")
            return ModelEndpoint(
                base_url=self.kong_url,
                model=actual_model,
                api_key=self.kong_api_key,
                is_paid=True,
                fallback_url=self.extreme_router_url,
                fallback_api_key=self.extreme_router_api_key,
            )

        # Free model (default path)
        if model_spec.startswith("free://"):
            alias = model_spec.removeprefix("free://")
        else:
            alias = model_spec

        resolved = self.alias_map.get(alias, alias)
        return ModelEndpoint(
            base_url=self.extreme_router_url,
            model=resolved,
            api_key=self.extreme_router_api_key,
            is_paid=False,
            fallback_url=self.kong_url,
            fallback_api_key=self.kong_api_key,
        )

    async def chat_completion(
        self,
        endpoint: ModelEndpoint,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> dict:
        """Make an OpenAI-compatible chat completion request with provider fallback."""
        payload = {
            "model": endpoint.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Try primary endpoint
        try:
            return await self._send_request(
                base_url=endpoint.base_url,
                api_key=endpoint.api_key,
                payload=payload,
            )
        except Exception as primary_err:
            if not endpoint.fallback_url:
                raise primary_err
            logger.warning(
                f"Primary provider request failed ({primary_err}), falling back to {endpoint.fallback_url}"
            )
            # Try fallback endpoint
            return await self._send_request(
                base_url=endpoint.fallback_url,
                api_key=endpoint.fallback_api_key,
                payload=payload,
            )

    async def _send_request(self, base_url: str, api_key: Optional[str], payload: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

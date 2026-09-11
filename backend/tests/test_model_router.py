"""Tests for the model router catalog + mock fallback (SPEC §9.2)."""

from __future__ import annotations

import pytest

from polyfloor.services.model_router import ModelRouterService, classify_tier, _mock_catalog


def test_classify_tier_reasoning():
    assert classify_tier("mimo-v2.5-pro") == "reasoning"
    assert classify_tier("o3-mini") == "fast"  # mini -> fast
    assert classify_tier("deepseek-r1") == "reasoning"


def test_classify_tier_frontier_and_fast():
    assert classify_tier("gpt-4o") == "frontier"
    assert classify_tier("claude-3-opus") == "frontier"
    assert classify_tier("gemini-1.5-flash") == "fast"
    assert classify_tier("some-free-7b") == "fast"


def test_mock_catalog_groups_and_includes_hr_model():
    catalog = _mock_catalog("mimo-v2.5-pro")
    assert set(catalog.keys()) == {"free", "fast", "reasoning", "frontier"}
    all_ids = [m["id"] for grp in catalog.values() for m in grp]
    assert "mimo-v2.5-pro" in all_ids


@pytest.mark.asyncio
async def test_router_falls_back_to_mock_when_unreachable():
    # Point at a closed port; must not raise, must return a mock catalog.
    service = ModelRouterService(
        endpoint="http://127.0.0.1:1/v1", api_key=None, default_hr_model="mimo-v2.5-pro"
    )
    catalog = await service.list_models()
    assert catalog["_source"] == "mock"
    assert "reasoning" in catalog

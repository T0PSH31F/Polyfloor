"""Model router tests — free-first routing, paid model gating."""

from __future__ import annotations

import pytest

from polyfloor.services.model_router import ModelRouter


@pytest.fixture
def router():
    return ModelRouter(
        extreme_router_url="https://router.example.com/v1",
        extreme_router_api_key="test-key",
        hermes_url="http://localhost:11434/v1",
        hermes_model="hermes3",
        reasoning_alias="qwen-2.5-72b",
        fast_alias="llama-3.1-8b",
        code_alias="deepseek-coder-v2",
        allow_paid=False,
    )


@pytest.fixture
def router_paid():
    return ModelRouter(
        extreme_router_url="https://router.example.com/v1",
        extreme_router_api_key="test-key",
        allow_paid=True,
    )


def test_free_reasoning_alias(router):
    ep = router.resolve("free://best-reasoning")
    assert ep.base_url == "https://router.example.com/v1"
    assert ep.model == "qwen-2.5-72b"
    assert not ep.is_paid
    assert ep.api_key == "test-key"


def test_free_fast_alias(router):
    ep = router.resolve("free://best-fast")
    assert ep.model == "llama-3.1-8b"
    assert not ep.is_paid


def test_free_code_alias(router):
    ep = router.resolve("free://best-code")
    assert ep.model == "deepseek-coder-v2"


def test_hermes_local(router):
    ep = router.resolve("hermes:llama3")
    assert ep.base_url == "http://localhost:11434/v1"
    assert ep.model == "llama3"
    assert ep.api_key is None
    assert not ep.is_paid


def test_hermes_default(router):
    ep = router.resolve("hermes:")
    assert ep.model == "hermes3"


def test_bare_alias_treated_as_free(router):
    ep = router.resolve("best-fast")
    assert ep.model == "llama-3.1-8b"
    assert not ep.is_paid


def test_paid_blocked_globally(router):
    with pytest.raises(ValueError, match="globally disabled"):
        router.resolve("paid://gpt-4o")


def test_paid_blocked_per_floor(router_paid):
    with pytest.raises(ValueError, match="not allowed for this floor"):
        router_paid.resolve("paid://gpt-4o", floor_paid_allowed=False)


def test_paid_allowed_when_both_gates(router_paid):
    ep = router_paid.resolve("paid://gpt-4o", floor_paid_allowed=True)
    assert ep.model == "gpt-4o"
    assert ep.is_paid


def test_unknown_alias_passes_through(router):
    ep = router.resolve("free://custom-model-xyz")
    assert ep.model == "custom-model-xyz"
    assert not ep.is_paid

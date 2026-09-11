"""Tests for the avatar composer (SPEC §9.3): determinism, tenant isolation, fallback."""

from __future__ import annotations

from polyfloor.assets.avatar_composer import (
    _deterministic_seed,
    _seeded_rng,
    avatar_file_path,
    compose_avatar,
    is_path_in_company,
)


def test_deterministic_seed_is_stable():
    a = _deterministic_seed("co_x", "agent_1")
    b = _deterministic_seed("co_x", "agent_1")
    c = _deterministic_seed("co_y", "agent_1")
    assert a == b
    assert a != c


def test_seeded_rng_is_deterministic():
    r1 = _seeded_rng(12345)
    r2 = _seeded_rng(12345)
    seq1 = [r1() for _ in range(5)]
    seq2 = [r2() for _ in range(5)]
    assert seq1 == seq2


def test_avatar_path_stays_in_company_workspace():
    path = avatar_file_path("co_isolated", "agent_7")
    assert is_path_in_company("co_isolated", path)
    # A path for a different company must NOT be considered inside this one.
    other = avatar_file_path("co_other", "agent_7")
    assert not is_path_in_company("co_isolated", other)


def test_compose_avatar_writes_file(tmp_path, monkeypatch):
    import polyfloor.assets.avatar_composer as ac

    monkeypatch.setattr(ac, "get_settings", lambda: _FakeSettings(str(tmp_path)))
    uri = compose_avatar("co_av", "agent_1", "worker")
    assert uri == "/api/companies/co_av/avatars/agent_1.png"
    out = tmp_path / "companies" / "co_av" / "avatars" / "agent_1.png"
    assert out.exists()


class _FakeSettings:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.static_dir = ""

    def router_api_key(self) -> None:
        return None

    def api_token(self) -> None:
        return None

    def cors_origins(self) -> list[str]:
        return []

    @property
    def default_hr_model(self) -> str:
        return "mimo-v2.5-pro"

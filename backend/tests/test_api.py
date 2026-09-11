"""HTTP API integration tests via httpx ASGITransport.

Covers the acceptance criteria: create company -> CEO/HR/teams/boards/gated path;
model list (mock); action dispatch; two companies isolated at the API layer.
"""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from polyfloor import db as db_mod
from polyfloor import main as main_mod
from polyfloor.config import get_settings


@pytest_asyncio.fixture
async def api_client(tmp_path, monkeypatch):
    """A fully isolated app instance backed by a temp-file SQLite DB."""
    db_file = tmp_path / "polyfloor_api.db"
    monkeypatch.setenv("POLYFLOOR_DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")
    monkeypatch.setenv("POLYFLOOR_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("POLYFLOOR_STATIC_DIR", "")

    # Reset cached settings + engine so the new env takes effect.
    get_settings.cache_clear()
    await db_mod.close_engine()

    await db_mod.init_db()
    transport = ASGITransport(app=main_mod.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await db_mod.close_engine()
    get_settings.cache_clear()


async def test_healthz(api_client):
    resp = await api_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_metrics_exposed(api_client):
    resp = await api_client.get("/metrics")
    assert resp.status_code == 200
    assert "polyfloor_" in resp.text


async def test_create_company_yields_full_org_and_gated_path(api_client):
    resp = await api_client.post(
        "/api/companies",
        json={"name": "Lumin Press", "goal": "ship a digital product", "template_id": "digital-products"},
    )
    assert resp.status_code == 201, resp.text
    company = resp.json()
    assert company["id"].startswith("co_lumin-press")

    state = await api_client.get(f"/api/companies/{company['id']}/state")
    assert state.status_code == 200
    snap = state.json()
    roles = {a["role"] for a in snap["agents"]}
    assert "ceo" in roles and "hr" in roles
    assert {"cfo", "cto", "coo", "cho"} <= roles
    assert any(a["role"] == "lead" for a in snap["agents"])
    titles = [t["title"] for t in snap["tasks"]]
    assert any("Research" in t for t in titles)
    assert any("Publish" in t for t in titles)
    assert any(a["policy_key"] == "publish" for a in snap["approvals"])


async def test_model_list_returns_grouped_catalog(api_client):
    resp = await api_client.get("/api/models")
    assert resp.status_code == 200
    catalog = resp.json()
    assert set(catalog.keys()) >= {"free", "fast", "reasoning", "frontier"}
    tiers = (catalog["free"], catalog["fast"], catalog["reasoning"], catalog["frontier"])
    all_ids = [m["id"] for grp in tiers for m in grp]
    assert "mimo-v2.5-pro" in all_ids


async def test_two_companies_isolated_at_api(api_client):
    a = await api_client.post("/api/companies", json={"name": "Alpha Co", "goal": "x"})
    b = await api_client.post("/api/companies", json={"name": "Beta Co", "goal": "y"})
    a_id, b_id = a.json()["id"], b.json()["id"]

    a_state = (await api_client.get(f"/api/companies/{a_id}/state")).json()
    b_state = (await api_client.get(f"/api/companies/{b_id}/state")).json()

    a_tasks = {t["company_id"] for t in a_state["tasks"]}
    b_tasks = {t["company_id"] for t in b_state["tasks"]}
    assert a_tasks == {a_id}
    assert b_tasks == {b_id}
    # Alpha's CEO must not appear in Beta's agent list.
    a_agent_ids = {x["id"] for x in a_state["agents"]}
    b_agent_ids = {x["id"] for x in b_state["agents"]}
    assert a_agent_ids.isdisjoint(b_agent_ids)


async def test_put_agent_model_rejects_cross_company(api_client):
    a = await api_client.post("/api/companies", json={"name": "ModelCo", "goal": "x"})
    a_id = a.json()["id"]
    # Attempt to reassign Alpha's CEO from a different company context.
    resp = await api_client.put(
        f"/api/agents/{a_id}_ceo/model?company_id=co_other",
        json={"model_id": "free-fast-1"},
    )
    assert resp.status_code == 404


async def test_advance_task_and_approve_publish(api_client):
    c = await api_client.post("/api/companies", json={"name": "FlowCo", "goal": "ship"})
    cid = c.json()["id"]
    state = (await api_client.get(f"/api/companies/{cid}/state")).json()
    ready = next(t for t in state["tasks"] if t["status"] == "READY")

    # Advance the first stage to completion.
    adv = await api_client.post(
        "/api/actions",
        json={"company_id": cid, "action": "advance_task", "target_type": "task", "target_id": str(ready["id"])},
    )
    assert adv.status_code == 200, adv.text

    # Resolve the publish approval (the gated irreversible action).
    publish_approval = next(
        a for a in (await api_client.get(f"/api/companies/{cid}/state")).json()["approvals"]
        if a["policy_key"] == "publish"
    )
    dec = await api_client.post(
        "/api/actions",
        json={"company_id": cid, "action": "approve", "target_type": "approval", "target_id": str(publish_approval["id"])},
    )
    assert dec.status_code == 200, dec.text
    assert dec.json()["result"]["approval"]["status"] == "APPROVED"

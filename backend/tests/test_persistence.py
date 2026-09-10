"""Tests for SQLModel persistence, data models, and restart durability."""

from __future__ import annotations

import json
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from polyfloor.db.models import ApiAuditLog, ApiToken, Approval, FloorEvent, Task
from polyfloor.services.event_bus import event_bus


@pytest.mark.asyncio
async def test_task_persistence(tmp_path):
    db_file = tmp_path / "test_polyfloor.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    engine1 = create_async_engine(db_url)
    async with engine1.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session1 = sessionmaker(engine1, class_=AsyncSession, expire_on_commit=False)
    async with async_session1() as session:
        task = Task(
            floor_id="production",
            title="Deploy new release",
            description="Run deployment script",
            status="queued",
            assigned_role="worker",
            priority=10,
            metadata_json=json.dumps({"sprint": 1}),
        )
        session.add(task)
        await session.commit()

    await engine1.dispose()

    # Re-open database (simulate restart)
    engine2 = create_async_engine(db_url)
    async_session2 = sessionmaker(engine2, class_=AsyncSession, expire_on_commit=False)
    async with async_session2() as session:
        stmt = select(Task).where(Task.floor_id == "production")
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        assert len(tasks) == 1
        assert tasks[0].title == "Deploy new release"
        assert tasks[0].status == "queued"
        assert json.loads(tasks[0].metadata_json) == {"sprint": 1}

    await engine2.dispose()


@pytest.mark.asyncio
async def test_event_bus_db_persistence(test_engine, test_session):
    from unittest.mock import patch
    from polyfloor.db import get_engine

    with patch("polyfloor.services.event_bus.get_engine", return_value=test_engine):
        await event_bus.publish(
            floor_id="research",
            event_type="experiment.completed",
            payload={"score": 0.95},
            actor="researcher_agent",
        )

    stmt = select(FloorEvent).where(FloorEvent.floor_id == "research")
    result = await test_session.execute(stmt)
    events = result.scalars().all()

    assert len(events) == 1
    assert events[0].event_type == "experiment.completed"
    assert events[0].actor == "researcher_agent"
    assert json.loads(events[0].payload_json) == {"score": 0.95}


@pytest.mark.asyncio
async def test_approval_persistence(test_session):
    approval = Approval(
        floor_id="marketing",
        task_id=42,
        approval_type="campaign_budget",
        description="Approve $500 ad spend",
        payload_json=json.dumps({"budget": 500}),
        requested_by="marketing_lead",
    )
    test_session.add(approval)
    await test_session.commit()

    stmt = select(Approval).where(Approval.id == approval.id)
    result = await test_session.execute(stmt)
    fetched = result.scalar_one()

    assert fetched.status == "pending"
    assert fetched.requested_by == "marketing_lead"
    assert json.loads(fetched.payload_json) == {"budget": 500}

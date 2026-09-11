"""Agent executor — the mock control loop for the MVP.

In production each agent (CEO, HR, leads, C-suite, QA panel) runs an
OpenAI-compatible loop against the router. For the OSS MVP the loop is mocked:
advancing a task emits a deterministic artifact and walks the pipeline one
stage. This keeps the research→spec→draft→QA→marketing path demonstrable
without live model calls. See SPEC §5, §6.3.
"""

from __future__ import annotations

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Artifact, CompanyContext, Task
from ..services import repository as repo
from ..services.event_bus import event_bus


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


async def advance_task(
    session: AsyncSession,
    ctx: CompanyContext,
    task_id: int,
    *,
    wip_limit: int = 3,
) -> Task:
    """Walk a task one step forward through the pipeline.

    BACKLOG/READY -> IN_PROGRESS -> REVIEW -> (QA passes) -> next stage.
    The publish stage stays AWAITING_APPROVAL (gated).
    """
    task = await repo.get_task(session, ctx, task_id)
    if task is None:
        raise LookupError(f"task {task_id} not found in company {ctx.company_id}")

    if task.status in ("BACKLOG", "READY"):
        task = await repo.transition_task(session, ctx, task_id, "IN_PROGRESS", wip_limit=wip_limit)
        await event_bus.publish(
            ctx,
            "task.started",
            {"task_id": task_id, "title": task.title, "owner": task.owner_agent_id},
            source_agent_id=task.owner_agent_id,
            correlation_id=str(task_id),
        )
        return task

    if task.status == "IN_PROGRESS":
        # Produce an artifact and move to REVIEW (QA gate).
        content = f"# {task.title}\n\nMock artifact for stage in company {ctx.company_id}."
        artifact = await repo.create_artifact(
            session,
            Artifact(
                company_id=ctx.company_id,
                task_id=task_id,
                type=task.title.split(" — ")[0].lower() if " — " in task.title else "document",
                title=task.title,
                uri=f"polyfloor://companies/{ctx.company_id}/tasks/{task_id}/artifact",
                content_hash=_hash(content),
                review_status="PENDING",
            ),
        )
        task.artifact_id = artifact.id
        session.add(task)
        await session.commit()
        task = await repo.transition_task(session, ctx, task_id, "REVIEW", wip_limit=wip_limit)
        await event_bus.publish(
            ctx,
            "artifact.produced",
            {"task_id": task_id, "artifact_id": artifact.id, "hash": artifact.content_hash},
            source_agent_id=task.owner_agent_id,
            correlation_id=str(task_id),
        )
        return task

    if task.status == "REVIEW":
        # QA panel mock: pass the artifact, advance toward the gate.
        if task.artifact_id is not None:
            art = await repo.get_artifact(session, ctx, task.artifact_id)
            if art is not None:
                art.review_status = "PASSED"
                session.add(art)
                await session.commit()
        # If a child task exists, mark it READY (unblock the next stage).
        next_task = await _find_child(session, ctx, task)
        if next_task is not None and next_task.status == "BACKLOG":
            await repo.transition_task(session, ctx, next_task.id, "READY", wip_limit=wip_limit)  # type: ignore[arg-type]
        task = await repo.transition_task(session, ctx, task_id, "DONE", wip_limit=wip_limit)
        await event_bus.publish(
            ctx,
            "task.done",
            {"task_id": task_id},
            source_agent_id=task.owner_agent_id,
            correlation_id=str(task_id),
        )
        return task

    return task


async def _find_child(session: AsyncSession, ctx: CompanyContext, parent: Task) -> Task | None:
    """Return the task whose parent is this one (next pipeline stage)."""
    tasks = await repo.list_tasks(session, ctx)
    for t in tasks:
        if t.parent_task_id == parent.id:
            return t
    return None

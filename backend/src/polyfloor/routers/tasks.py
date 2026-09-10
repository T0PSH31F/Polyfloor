"""Task management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import Principal, require_floor_access, require_scope
from ..db import get_pool

router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_TRANSITIONS = {
    "backlog": {"queued"},
    "queued": {"in_progress", "backlog"},
    "in_progress": {"staging", "rejected", "queued"},
    "staging": {"done", "rejected", "in_progress"},
    "rejected": {"backlog", "queued"},
    "done": {"backlog"},
}


class TaskCreate(BaseModel):
    floor_id: str
    title: str
    description: str = ""
    sprint_id: int | None = None
    assigned_role: str | None = None
    priority: int = 0
    metadata: dict[str, Any] = {}


class TaskResponse(BaseModel):
    id: int
    floor_id: str
    sprint_id: int | None
    title: str
    description: str
    status: str
    assigned_role: str | None
    priority: int
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class TaskUpdate(BaseModel):
    status: str | None = None
    assigned_role: str | None = None
    priority: int | None = None
    metadata: dict[str, Any] | None = None


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    floor_id: str | None = None,
    status: str | None = None,
    principal: Principal = Depends(require_scope("tasks:read")),
):
    """List tasks, optionally filtered by floor and status."""
    pool = await get_pool()
    conditions: list[str] = []
    params: list[Any] = []
    idx = 1

    if floor_id:
        require_floor_access(floor_id, principal)
        conditions.append(f"floor_id = ${idx}")
        params.append(floor_id)
        idx += 1

    if status:
        conditions.append(f"status = ${idx}")
        params.append(status)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM tower.tasks {where} ORDER BY priority DESC, created_at DESC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [
        TaskResponse(
            id=r["id"],
            floor_id=r["floor_id"],
            sprint_id=r["sprint_id"],
            title=r["title"],
            description=r["description"],
            status=r["status"],
            assigned_role=r["assigned_role"],
            priority=r["priority"],
            metadata=r["metadata"],
            created_at=r["created_at"].isoformat(),
            updated_at=r["updated_at"].isoformat(),
        )
        for r in rows
    ]


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    principal: Principal = Depends(require_scope("tasks:write")),
):
    """Create a new task."""
    require_floor_access(task.floor_id, principal)
    pool = await get_pool()

    import json

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO tower.tasks (floor_id, title, description, sprint_id, assigned_role, priority, metadata) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *",
            task.floor_id,
            task.title,
            task.description,
            task.sprint_id,
            task.assigned_role,
            task.priority,
            json.dumps(task.metadata),
        )

    # Audit
    await _emit_event(
        pool,
        task.floor_id,
        "task.created",
        principal.role.value,
        {"task_id": row["id"], "title": task.title},
    )

    return TaskResponse(
        id=row["id"],
        floor_id=row["floor_id"],
        sprint_id=row["sprint_id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        assigned_role=row["assigned_role"],
        priority=row["priority"],
        metadata=row["metadata"],
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    update: TaskUpdate,
    principal: Principal = Depends(require_scope("tasks:write")),
):
    """Update a task. Status transitions are validated server-side."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM tower.tasks WHERE id = $1", task_id)

    if existing is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    require_floor_access(existing["floor_id"], principal)

    # Validate status transition
    if update.status is not None:
        current = existing["status"]
        allowed = VALID_TRANSITIONS.get(current, set())
        if update.status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition: {current} -> {update.status}. Allowed: {allowed}",
            )

    import json

    fields: dict[str, Any] = {}
    if update.status is not None:
        fields["status"] = update.status
    if update.assigned_role is not None:
        fields["assigned_role"] = update.assigned_role
    if update.priority is not None:
        fields["priority"] = update.priority
    if update.metadata is not None:
        fields["metadata"] = json.dumps(update.metadata)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_parts = []
    params: list[Any] = []
    idx = 1
    for key, val in fields.items():
        set_parts.append(f"{key} = ${idx}")
        params.append(val)
        idx += 1

    params.append(task_id)
    query = f"UPDATE tower.tasks SET {', '.join(set_parts)} WHERE id = ${idx} RETURNING *"

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *params)

    await _emit_event(
        pool, row["floor_id"], "task.updated", principal.role.value, {"task_id": task_id, **fields}
    )

    return TaskResponse(
        id=row["id"],
        floor_id=row["floor_id"],
        sprint_id=row["sprint_id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        assigned_role=row["assigned_role"],
        priority=row["priority"],
        metadata=row["metadata"],
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


async def _emit_event(pool, floor_id: str, event_type: str, actor: str, payload: dict):
    import json

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO tower.events (floor_id, event_type, actor, payload) VALUES ($1, $2, $3, $4)",
            floor_id,
            event_type,
            actor,
            json.dumps(payload),
        )

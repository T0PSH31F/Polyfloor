"""Approval queue endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import Principal, require_floor_access, require_scope
from ..db import get_pool

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalCreate(BaseModel):
    floor_id: str
    task_id: int | None = None
    approval_type: str
    description: str
    payload: dict[str, Any] = {}
    requested_by: str


class ApprovalResponse(BaseModel):
    id: int
    floor_id: str
    task_id: int | None
    approval_type: str
    description: str
    payload: dict[str, Any]
    status: str
    requested_by: str
    resolved_by: str | None
    created_at: str
    resolved_at: str | None


class ApprovalResolve(BaseModel):
    status: str  # "approved" or "rejected"
    resolved_by: str


@router.get("", response_model=list[ApprovalResponse])
async def list_approvals(
    floor_id: str | None = None,
    status: str | None = None,
    principal: Principal = Depends(require_scope("approvals:read")),
):
    """List approvals, optionally filtered."""
    pool = await get_pool()
    conditions: list[str] = []
    params: list[Any] = []
    idx = 1

    if floor_id:
        require_floor_access(floor_id, principal)
        conditions.append(f"a.floor_id = ${idx}")
        params.append(floor_id)
        idx += 1

    if status:
        conditions.append(f"a.status = ${idx}")
        params.append(status)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM tower.approvals a {where} ORDER BY a.created_at DESC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [
        ApprovalResponse(
            id=r["id"],
            floor_id=r["floor_id"],
            task_id=r["task_id"],
            approval_type=r["approval_type"],
            description=r["description"],
            payload=r["payload"],
            status=r["status"],
            requested_by=r["requested_by"],
            resolved_by=r["resolved_by"],
            created_at=r["created_at"].isoformat(),
            resolved_at=r["resolved_at"].isoformat() if r["resolved_at"] else None,
        )
        for r in rows
    ]


@router.post("", response_model=ApprovalResponse, status_code=201)
async def create_approval(
    approval: ApprovalCreate,
    principal: Principal = Depends(require_scope("approvals:create")),
):
    """Create a new approval request."""
    require_floor_access(approval.floor_id, principal)
    pool = await get_pool()

    import json

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO tower.approvals (floor_id, task_id, approval_type, description, payload, requested_by) "
            "VALUES ($1, $2, $3, $4, $5, $6) RETURNING *",
            approval.floor_id,
            approval.task_id,
            approval.approval_type,
            approval.description,
            json.dumps(approval.payload),
            approval.requested_by,
        )

    return ApprovalResponse(
        id=row["id"],
        floor_id=row["floor_id"],
        task_id=row["task_id"],
        approval_type=row["approval_type"],
        description=row["description"],
        payload=row["payload"],
        status=row["status"],
        requested_by=row["requested_by"],
        resolved_by=row["resolved_by"],
        created_at=row["created_at"].isoformat(),
        resolved_at=row["resolved_at"].isoformat() if row["resolved_at"] else None,
    )


@router.post("/{approval_id}/resolve", response_model=ApprovalResponse)
async def resolve_approval(
    approval_id: int,
    resolution: ApprovalResolve,
    principal: Principal = Depends(require_scope("approvals:resolve")),
):
    """Resolve (approve/reject) an approval. Human/admin only."""
    if resolution.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE tower.approvals SET status = $1, resolved_by = $2, resolved_at = NOW() "
            "WHERE id = $3 AND status = 'pending' RETURNING *",
            resolution.status,
            resolution.resolved_by,
            approval_id,
        )

    if row is None:
        raise HTTPException(status_code=404, detail=f"Pending approval {approval_id} not found")

    require_floor_access(row["floor_id"], principal)

    import json

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO tower.events (floor_id, event_type, actor, payload) VALUES ($1, $2, $3, $4)",
            row["floor_id"],
            "approval.resolved",
            resolution.resolved_by,
            json.dumps({"approval_id": approval_id, "status": resolution.status}),
        )

    return ApprovalResponse(
        id=row["id"],
        floor_id=row["floor_id"],
        task_id=row["task_id"],
        approval_type=row["approval_type"],
        description=row["description"],
        payload=row["payload"],
        status=row["status"],
        requested_by=row["requested_by"],
        resolved_by=row["resolved_by"],
        created_at=row["created_at"].isoformat(),
        resolved_at=row["resolved_at"].isoformat() if row["resolved_at"] else None,
    )

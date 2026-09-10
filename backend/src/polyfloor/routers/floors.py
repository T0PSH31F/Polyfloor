"""Floor configuration endpoints."""

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import Principal, require_floor_access, require_scope
from ..db import get_pool

router = APIRouter(prefix="/floors", tags=["floors"])


class FloorConfigResponse(BaseModel):
    id: str
    display_name: str
    email: str | None
    org_name: str
    timezone: str
    target_machine: str | None
    db_schema: str
    mcps: list[str]
    template: str | None
    paid_models_allowed: bool
    daily_budget_usd: float
    persist_paths: list[str]
    config_json: dict[str, Any]
    version: int


class FloorConfigUpdate(BaseModel):
    config_json: dict[str, Any] | None = None
    display_name: str | None = None
    email: str | None = None
    timezone: str | None = None
    paid_models_allowed: bool | None = None
    daily_budget_usd: float | None = None


class RoleResponse(BaseModel):
    role_name: str
    enable: bool
    model: str
    max_tokens: int
    description: str


class RoleUpdate(BaseModel):
    enable: bool | None = None
    model: str | None = None
    max_tokens: int | None = None
    description: str | None = None


@router.get("", response_model=list[FloorConfigResponse])
async def list_floors(
    principal: Principal = Depends(require_scope("floors:read")),
):
    """List all floor configurations."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tower.floor_configs ORDER BY id")
    return [FloorConfigResponse(**dict(r)) for r in rows]


@router.get("/{floor_id}", response_model=FloorConfigResponse)
async def get_floor(
    floor_id: str,
    principal: Principal = Depends(require_scope("floors:read")),
):
    """Get a specific floor configuration."""
    require_floor_access(floor_id, principal)
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tower.floor_configs WHERE id = $1", floor_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Floor '{floor_id}' not found")
    return FloorConfigResponse(**dict(row))


@router.get("/{floor_id}/config", response_model=FloorConfigResponse)
async def get_floor_config(
    floor_id: str,
    principal: Principal = Depends(require_scope("floors:read")),
):
    """Get floor configuration (alias for GET /floors/{id})."""
    return await get_floor(floor_id, principal)


@router.put("/{floor_id}/config", response_model=FloorConfigResponse)
async def update_floor_config(
    floor_id: str,
    update: FloorConfigUpdate,
    principal: Principal = Depends(require_scope("config:write")),
):
    """Update floor configuration. HR/admin scope required."""
    require_floor_access(floor_id, principal)
    pool = await get_pool()

    # Build dynamic SET clause
    fields: dict[str, Any] = {}
    if update.config_json is not None:
        fields["config_json"] = update.config_json
    if update.display_name is not None:
        fields["display_name"] = update.display_name
    if update.email is not None:
        fields["email"] = update.email
    if update.timezone is not None:
        fields["timezone"] = update.timezone
    if update.paid_models_allowed is not None:
        fields["paid_models_allowed"] = update.paid_models_allowed
    if update.daily_budget_usd is not None:
        fields["daily_budget_usd"] = update.daily_budget_usd

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Increment version, set updated_by
    fields["version"] = "version + 1"
    fields["updated_by"] = principal.role.value

    set_parts = []
    values: list[Any] = []
    idx = 1
    for key, val in fields.items():
        if key == "version":
            set_parts.append("version = version + 1")
        else:
            set_parts.append(f"{key} = ${idx}")
            values.append(val)
            idx += 1

    values.append(floor_id)
    query = f"""
        UPDATE tower.floor_configs
        SET {", ".join(set_parts)}
        WHERE id = ${idx}
        RETURNING *
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *values)

    if row is None:
        raise HTTPException(status_code=404, detail=f"Floor '{floor_id}' not found")

    # Audit event
    await _emit_event(pool, floor_id, "config.updated", principal.role.value, fields)

    return FloorConfigResponse(**dict(row))


@router.get("/{floor_id}/roles", response_model=list[RoleResponse])
async def list_roles(
    floor_id: str,
    principal: Principal = Depends(require_scope("roles:read")),
):
    """List roles for a floor."""
    require_floor_access(floor_id, principal)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role_name, enable, model, max_tokens, description "
            "FROM tower.roles WHERE floor_id = $1 ORDER BY role_name",
            floor_id,
        )
    return [RoleResponse(**dict(r)) for r in rows]


@router.put("/{floor_id}/roles/{role_name}", response_model=RoleResponse)
async def update_role(
    floor_id: str,
    role_name: str,
    update: RoleUpdate,
    principal: Principal = Depends(require_scope("roles:write")),
):
    """Update a specific role. HR/admin scope required."""
    require_floor_access(floor_id, principal)
    pool = await get_pool()

    fields: dict[str, Any] = {}
    if update.enable is not None:
        fields["enable"] = update.enable
    if update.model is not None:
        fields["model"] = update.model
    if update.max_tokens is not None:
        fields["max_tokens"] = update.max_tokens
    if update.description is not None:
        fields["description"] = update.description

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_parts = []
    values: list[Any] = []
    idx = 1
    for key, val in fields.items():
        set_parts.append(f"{key} = ${idx}")
        values.append(val)
        idx += 1

    values.extend([floor_id, role_name])
    query = f"""
        UPDATE tower.roles
        SET {", ".join(set_parts)}
        WHERE floor_id = ${idx} AND role_name = ${idx + 1}
        RETURNING role_name, enable, model, max_tokens, description
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *values)

    if row is None:
        raise HTTPException(
            status_code=404, detail=f"Role '{role_name}' not found on floor '{floor_id}'"
        )

    await _emit_event(
        pool, floor_id, "role.updated", principal.role.value, {"role": role_name, **fields}
    )

    return RoleResponse(**dict(row))


async def _emit_event(
    pool: asyncpg.Pool, floor_id: str, event_type: str, actor: str, payload: dict
):
    """Insert an audit event."""
    import json

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO tower.events (floor_id, event_type, actor, payload) VALUES ($1, $2, $3, $4)",
            floor_id,
            event_type,
            actor,
            json.dumps(payload),
        )

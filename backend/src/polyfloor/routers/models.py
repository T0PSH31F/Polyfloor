"""Model catalog and per-agent model assignment endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import company_context
from ..db import get_session
from ..db.models import CompanyContext
from ..services import repository as repo
from ..services.model_router import ModelRouterService

router = APIRouter(tags=["models"])


class AgentModelUpdate(BaseModel):
    model_id: str


@router.get("/models")
async def list_models() -> dict:
    """Enumerate router models grouped as free|fast|reasoning|frontier.

    Falls back to a marked mock catalog (including the configured HR model)
    when the router is unreachable.
    """
    service = ModelRouterService()
    return await service.list_models()


@router.put("/agents/{agent_id}/model")
async def update_agent_model(
    agent_id: str,
    body: AgentModelUpdate,
    company_id: str = Depends(company_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Change an agent's model at runtime, scoped to the agent's company."""
    ctx: CompanyContext = company_id  # type: ignore[assignment]
    try:
        agent = await repo.update_agent_model(session, ctx, agent_id, body.model_id)
    except LookupError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"agent {agent_id} not found in company {ctx.company_id}",
        ) from None
    return {"agent": agent.model_dump()}

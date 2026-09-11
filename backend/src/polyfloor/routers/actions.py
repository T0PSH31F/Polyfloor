"""Action dispatch endpoint.

The user (or CEO) sends commands via ``POST /api/actions``. Every action is
company-scoped; irreversible actions route through the approval queue. See
SPEC §8.5, §6.4.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..db.models import CompanyContext
from .companies import dispatch_action

router = APIRouter(tags=["actions"])


class ActionRequest(BaseModel):
    company_id: str
    action: str  # approve | reject | pause | resume | stop | advance_task | request_hire | execute_hire
    target_type: str = "approval"  # approval | agent | task | team
    target_id: str
    payload: dict[str, Any] = {}


@router.post("/actions")
async def post_action(
    body: ActionRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    ctx = CompanyContext(body.company_id, actor="user")
    try:
        result = await dispatch_action(
            session, ctx, body.action, body.target_type, body.target_id, body.payload
        )
        await session.commit()
        return {"ok": True, "result": result}
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"missing field: {exc}") from exc

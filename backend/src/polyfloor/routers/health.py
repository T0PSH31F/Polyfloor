"""Health and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response

from ..observability import metrics_text

router = APIRouter()


@router.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics", tags=["observability"])
async def metrics() -> Response:
    return Response(content=metrics_text(), media_type="text/plain; version=0.0.4")

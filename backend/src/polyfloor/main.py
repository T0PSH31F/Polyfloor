"""Polyfloor FastAPI application entry point."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import close_pool, get_pool
from .routers import approvals, events, floors, health, tasks

logger = structlog.get_logger()


def _parse_origins(raw: str) -> list[str]:
    """Parse comma-separated CORS origins."""
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: manage DB pool lifecycle."""
    settings = get_settings()
    logger.info("polyfloor.starting", host=settings.host, port=settings.port)
    try:
        await get_pool()
        logger.info("polyfloor.db_connected")
    except Exception as e:
        logger.warning("polyfloor.db_unavailable", error=str(e))
    yield
    await close_pool()
    logger.info("polyfloor.stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Polyfloor",
        description="Multi-floor AI company OS — Tower API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    origins = _parse_origins(settings.security.allowed_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        import uuid

        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Routers
    app.include_router(health.router)
    app.include_router(floors.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(approvals.router, prefix="/api/v1")
    app.include_router(events.router, prefix="/api/v1")

    return app


app = create_app()


def cli():
    """CLI entry point for uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "polyfloor.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    cli()

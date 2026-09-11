"""Polyfloor FastAPI application entry point.

Mounts all routers under ``/api`` (and ``/`` for health/metrics), serves the
built frontend SPA from ``POLYFLOOR_STATIC_DIR`` when present (``nix run``), and
runs the SQLite WAL database on startup.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import close_engine, get_engine, init_db
from .routers import actions, companies, events, health, models

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("polyfloor.starting", host=settings.host, port=settings.port)
    try:
        await init_db()
        logger.info("polyfloor.db_initialized", url=settings.database_url)
    except Exception as exc:  # pragma: no cover
        logger.error("polyfloor.db_init_failed", error=str(exc))
    with suppress(Exception):
        get_engine()
    yield
    await close_engine()
    logger.info("polyfloor.stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Polyfloor",
        description="Autonomous multi-company enterprise engine with a GBA/DS department-store UI.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Company-Id", "X-Actor", "X-Trace-Id"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):  # type: ignore[no-untyped-def]
        logger.error("polyfloor.unhandled_error", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": str(exc)},
        )

    # API routers.
    app.include_router(health.router)
    app.include_router(companies.router, prefix="/api")
    app.include_router(models.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(actions.router, prefix="/api")

    # Serve the built frontend SPA when a static dir is configured (nix run).
    static_dir = settings.static_dir
    if static_dir and Path(static_dir).is_dir():
        index_path = Path(static_dir) / "index.html"

        app.mount(
            "/assets",
            StaticFiles(directory=Path(static_dir) / "assets"),
            name="assets",
        )

        @app.get("/{path:path}")
        async def spa(path: str):  # type: ignore[no-untyped-def]
            # Don't shadow API routes.
            if path.startswith("api") or path.startswith("healthz") or path.startswith("metrics"):
                return JSONResponse({"error": "not found"}, status_code=404)
            candidate = Path(static_dir) / path
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_path)

    return app


app = create_app()


def cli() -> None:
    """CLI entry point for ``polyfloor`` / ``nix run``."""
    settings = get_settings()
    uvicorn.run(
        "polyfloor.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    cli()

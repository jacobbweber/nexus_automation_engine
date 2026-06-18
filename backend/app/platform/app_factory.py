"""Application factory — assembles the FastAPI app from platform + context routers.

Context api routers are registered here as they are built (M2+). Today it wires health,
CORS, the error handler, and database lifespan.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.contexts.connectors.api import routes as connectors_routes
from app.platform import health
from app.platform.config import get_settings
from app.platform.database import dispose_db, init_db
from app.platform.errors import register_error_handlers


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    init_db()
    yield
    dispose_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    # Platform routes + context routers under /api/v1.
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(connectors_routes.router, prefix="/api/v1")

    return app

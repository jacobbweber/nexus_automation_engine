"""Application factory — assembles the FastAPI app from platform + context routers.

Context api routers are registered here as they are built (M2+). Today it wires health,
CORS, the error handler, and database lifespan.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.contexts.automation_catalog.api import routes as catalog_routes
from app.contexts.connectors.api import routes as connectors_routes
from app.contexts.execution_engine.api import routes as execution_routes
from app.contexts.identity_access.api import routes as identity_routes
from app.platform import health
from app.platform.config import get_settings
from app.platform.database import dispose_db, init_db
from app.platform.errors import register_error_handlers


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    init_db()
    # Default users always seeded (idempotent) so auth works out of the box.
    from app.contexts.identity_access.application.service import seed_default_users

    seed_default_users()
    if get_settings().seed_demo_data:
        from app.contexts.automation_catalog.application.seed import seed_templates
        from app.contexts.execution_engine.application.seed import seed_history

        seed_templates()
        seed_history()
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
    app.include_router(identity_routes.router, prefix="/api/v1")
    app.include_router(connectors_routes.router, prefix="/api/v1")
    app.include_router(catalog_routes.router, prefix="/api/v1")
    app.include_router(execution_routes.router, prefix="/api/v1")

    return app

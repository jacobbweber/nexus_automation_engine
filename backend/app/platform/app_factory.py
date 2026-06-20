"""Application factory — assembles the FastAPI app from platform + context routers.

Context api routers are registered here as they are built (M2+). Today it wires health,
CORS, the error handler, and database lifespan.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope

from app.contexts.automation_catalog.api import routes as catalog_routes
from app.contexts.change_management.api import routes as change_routes
from app.contexts.cmdb.api import routes as cmdb_routes
from app.contexts.compliance.api import routes as compliance_routes
from app.contexts.connectors.api import routes as connectors_routes
from app.contexts.execution_engine.api import routes as execution_routes
from app.contexts.identity_access.api import routes as identity_routes
from app.contexts.incident_management.api import routes as incident_routes
from app.contexts.lifecycle_validation.api import routes as validation_routes
from app.contexts.orchestration_canvas.api import routes as canvas_routes
from app.contexts.review.api import routes as review_routes
from app.contexts.scheduling.api import routes as scheduling_routes
from app.platform import health
from app.platform.config import get_settings
from app.platform.database import dispose_db, init_db
from app.platform.errors import register_error_handlers
from app.platform.security_middleware import register_security_middleware
from app.platform.theming import routes as theming_routes


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    init_db()
    # Default users always seeded (idempotent) so auth works out of the box.
    from app.contexts.identity_access.application.service import seed_default_users
    from app.contexts.lifecycle_validation.application.service import seed_default_policy

    seed_default_users()
    seed_default_policy()  # the single admin-editable validation gate

    # Crash-recovery sweep (architecture audit A1): a previous process's in-flight runs are gone;
    # mark orphaned PENDING/RUNNING jobs + RUNNING workflow runs as FAILED so state is honest.
    from app.contexts.execution_engine.infrastructure.repository import JobRepository
    from app.contexts.orchestration_canvas.infrastructure.repository import CanvasRepository

    JobRepository().fail_orphaned_running()
    CanvasRepository().fail_orphaned_runs()
    if get_settings().seed_demo_data:
        from app.contexts.automation_catalog.application.seed import seed_templates
        from app.contexts.change_management.application.service import seed_change_management
        from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
        from app.contexts.execution_engine.application.seed import seed_history
        from app.contexts.incident_management.application.seed import seed_incidents
        from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

        seed_templates()
        seed_change_management()
        seed_cmdb_schemas()  # CMDB-as-contract: CI type schemas
        seed_cmdb_lineage()  # required relationships per CI type
        seed_history()
        seed_workflow_library()
        seed_incidents()  # open a triage board from the seeded failures

    scheduler_task = None
    if get_settings().scheduler_enabled:
        import asyncio

        from app.contexts.scheduling.application.service import scheduler_loop

        scheduler_task = asyncio.create_task(scheduler_loop(get_settings().scheduler_tick_seconds))
    yield
    if scheduler_task is not None:
        scheduler_task.cancel()
    dispose_db()


_DEFAULT_JWT_SECRET = "dev-only-not-a-secret-change-me-in-prod"


class SpaStaticFiles(StaticFiles):
    """StaticFiles that falls back to index.html for unknown paths.

    A single-page app owns its own client-side routing, so a hard refresh or deep link to a
    client route (e.g. ``/catalog``) must still return ``index.html`` rather than a 404 — the
    JS router then renders the right view. Real files (assets) are served verbatim; only a
    missing path triggers the fallback. API routes are registered before this mount, so they
    are never reached here.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            # Never mask an unknown API route with the SPA shell — those stay JSON 404s.
            # StaticFiles normalizes separators per-OS, so compare on the first path segment.
            first_segment = path.replace("\\", "/").lstrip("/").split("/", 1)[0]
            if exc.status_code == 404 and first_segment != "api":
                return await super().get_response("index.html", scope)
            raise


def create_app(static_dir: str | None = None) -> FastAPI:
    settings = get_settings()
    # Security audit S2: never run a non-local environment on the dev JWT secret.
    if settings.environment not in ("local", "test") and settings.jwt_secret == _DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "NEXUS_JWT_SECRET must be set to a strong secret outside local/test environments"
        )
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
    register_security_middleware(app)

    # Platform routes + context routers under /api/v1.
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(identity_routes.router, prefix="/api/v1")
    app.include_router(connectors_routes.router, prefix="/api/v1")
    app.include_router(catalog_routes.router, prefix="/api/v1")
    app.include_router(change_routes.router, prefix="/api/v1")
    app.include_router(cmdb_routes.router, prefix="/api/v1")
    app.include_router(compliance_routes.router, prefix="/api/v1")
    app.include_router(review_routes.router, prefix="/api/v1")
    app.include_router(execution_routes.router, prefix="/api/v1")
    app.include_router(canvas_routes.router, prefix="/api/v1")
    app.include_router(scheduling_routes.router, prefix="/api/v1")
    app.include_router(incident_routes.router, prefix="/api/v1")
    app.include_router(validation_routes.router, prefix="/api/v1")
    app.include_router(theming_routes.router, prefix="/api/v1")

    # Optionally serve the built SPA from the same origin (single-container deploy). The SPA-aware
    # static handler falls back to index.html so client-side deep links survive a hard refresh.
    spa_dir = static_dir or settings.static_dir
    if spa_dir and os.path.isdir(spa_dir):
        app.mount("/", SpaStaticFiles(directory=spa_dir, html=True), name="spa")

    return app

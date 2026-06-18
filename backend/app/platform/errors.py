"""Maps domain/application errors to HTTP responses at the edge.

Keeps FastAPI/HTTP concerns out of the contexts: domain code raises ``NexusError`` subclasses;
this handler translates them. Registered by the app factory.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared_kernel.errors import NexusError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NexusError)
    async def _handle_nexus_error(_request: Request, exc: NexusError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "detail": exc.message},
        )

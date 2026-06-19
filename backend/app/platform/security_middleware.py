"""Security middleware: response hardening headers + a request body-size limit (audit S3)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

_MAX_BODY_BYTES = 5 * 1024 * 1024  # 5 MiB

_CSP = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'"
_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": _CSP,
}


def register_security_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _security(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cl = request.headers.get("content-length")
        if cl is not None and cl.isdigit() and int(cl) > _MAX_BODY_BYTES:
            return JSONResponse(status_code=413, content={"error": "PayloadTooLarge"})
        response = await call_next(request)
        for key, value in _HEADERS.items():
            response.headers.setdefault(key, value)
        return response

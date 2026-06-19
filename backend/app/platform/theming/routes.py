"""Theming REST + change stream. GET is open (non-sensitive presentational data); writes require
auth. The change stream lets the UI hot-reload themes when the volume changes."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.contexts.identity_access.api.deps import get_current_user
from app.contexts.identity_access.domain.models import UserContext
from app.platform.theming import service

router = APIRouter(prefix="/themes", tags=["theming"])


class ThemesResponse(BaseModel):
    themes: list[dict]
    revision: float


@router.get("", response_model=ThemesResponse)
def list_themes() -> ThemesResponse:
    return ThemesResponse(themes=service.list_themes(), revision=service.revision())


@router.post("")
def save_theme(theme: dict, _user: UserContext = Depends(get_current_user)) -> dict:
    result = service.save_theme(theme)
    if not result.ok:
        raise HTTPException(
            status_code=422, detail={"errors": result.errors, "warnings": result.warnings}
        )
    return {
        "status": "saved",
        "id": service.slug(str(theme.get("id", ""))),
        "warnings": result.warnings,
    }


@router.delete("/{theme_id}")
def delete_theme(theme_id: str, _user: UserContext = Depends(get_current_user)) -> dict:
    return {"deleted": service.delete_theme(theme_id)}


@router.get("/stream")
async def stream_themes() -> StreamingResponse:
    """SSE: emits `theme:changed` whenever the themes volume revision changes."""

    async def gen() -> AsyncIterator[bytes]:
        last = service.revision()
        yield b": connected\n\n"
        with contextlib.suppress(asyncio.CancelledError):
            while True:
                await asyncio.sleep(2)
                rev = service.revision()
                if rev != last:
                    last = rev
                    yield f"event: theme:changed\ndata: {rev}\n\n".encode()
                else:
                    yield b": keep-alive\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

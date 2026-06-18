"""ASGI entrypoint. Run with: ``uvicorn app.main:app --reload`` from ``backend/``."""

from __future__ import annotations

from app.platform.app_factory import create_app

app = create_app()

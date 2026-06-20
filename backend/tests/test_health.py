"""Smoke test for the platform app: it builds, runs lifespan, and serves /health."""

from __future__ import annotations

from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def test_health_endpoint():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"]
    assert "simulation_mode" in body


def test_platform_status_reports_runtime():
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/platform/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["db_ok"] is True
    assert body["uptime_seconds"] >= 0
    assert {"app", "version", "scheduler_enabled", "workflows", "jobs"} <= body.keys()


def test_openapi_available():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200

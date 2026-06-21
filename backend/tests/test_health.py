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


def test_export_bundle_requires_admin():
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/platform/export").status_code == 401
        admin = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        ).json()["access_token"]
        operator = client.post(
            "/api/v1/auth/login", json={"username": "operator", "password": "operator123"}
        ).json()["access_token"]
        # non-admin is forbidden
        assert (
            client.get(
                "/api/v1/platform/export", headers={"Authorization": f"Bearer {operator}"}
            ).status_code
            == 403
        )
        ok = client.get("/api/v1/platform/export", headers={"Authorization": f"Bearer {admin}"})
        assert ok.status_code == 200
        body = ok.json()
        assert body["bundle_schema"] == "nexus-export/v1"
        assert {"workflows", "themes", "schedules", "exported_at"} <= body.keys()


def test_openapi_available():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api-openapi.json")
    assert resp.status_code == 200


def test_interactive_docs_do_not_shadow_spa_docs_route():
    """FastAPI's Swagger UI must not own /docs — that path belongs to the SPA surface.

    Regression: a hard-load/deep-link to /docs used to serve Swagger UI (then blanked by
    CSP) instead of the app. The interactive API docs now live under /api-docs.
    """
    app = create_app()
    with TestClient(app) as client:
        # No static dir is configured in tests, so /docs has no handler at all (404),
        # leaving it free for the SPA's index.html fallback in production.
        assert client.get("/docs").status_code == 404
        # The interactive docs are reachable at their relocated paths.
        assert client.get("/api-docs").status_code == 200
        assert client.get("/api-redoc").status_code == 200

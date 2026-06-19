"""Tests for security hardening (audit S3): headers + SSRF guard."""

from __future__ import annotations

import pytest
from app.contexts.connectors.domain.ports import ConnectorError
from app.contexts.orchestration_canvas.application.node_actions import _ssrf_guard
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def test_security_headers_present():
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert "content-security-policy" in resp.headers


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://127.0.0.1:8000/admin",  # loopback
        "http://10.1.2.3/internal",  # private
        "http://localhost/secret",  # localhost by name
    ],
)
def test_ssrf_guard_blocks_dangerous_hosts(url):
    with pytest.raises(ConnectorError):
        _ssrf_guard(url)


def test_ssrf_guard_allows_when_configured(monkeypatch):
    import os

    from app.platform.config import get_settings

    os.environ["NEXUS_HTTP_ALLOW_PRIVATE"] = "true"
    get_settings.cache_clear()
    try:
        _ssrf_guard("http://10.1.2.3/internal")  # should not raise
    finally:
        os.environ["NEXUS_HTTP_ALLOW_PRIVATE"] = "false"
        get_settings.cache_clear()

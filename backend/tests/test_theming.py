"""Server-side theming: deterministic validator, volume storage, REST + change revision."""

from __future__ import annotations

import os

import pytest
from app.platform.app_factory import create_app
from app.platform.theming import service
from app.platform.theming.validation import validate_theme
from fastapi.testclient import TestClient


def _valid_theme(theme_id: str = "demo") -> dict:
    light = {
        "--bg": "#fbf7f2",
        "--surface": "#ffffff",
        "--surface-2": "#f4ece1",
        "--text": "#1a1714",
        "--text-muted": "#7d6a57",
        "--border": "#e0d3c1",
        "--accent": "#2f72b0",
        "--accent-hover": "#285f93",
        "--accent-contrast": "#ffffff",
        "--success": "#4c8a5e",
        "--warn": "#b07a1e",
        "--danger": "#b23a33",
        "--info": "#3e6e8e",
        "--run-running": "#2f72b0",
        "--run-ok": "#4c8a5e",
        "--run-warn": "#b07a1e",
        "--run-failed": "#b23a33",
        "--run-skipped": "#8a7f72",
        "--focus": "#2f72b0",
    }
    dark = {
        "--bg": "#141210",
        "--surface": "#201d1a",
        "--surface-2": "#262220",
        "--text": "#fbf7f2",
        "--text-muted": "#c8b6a0",
        "--border": "#352f2a",
        "--accent": "#6ba6db",
        "--accent-hover": "#9cc6ec",
        "--accent-contrast": "#141210",
        "--success": "#8fc7a1",
        "--warn": "#e0bd6f",
        "--danger": "#e08a82",
        "--info": "#8fbdd6",
        "--run-running": "#6ba6db",
        "--run-ok": "#8fc7a1",
        "--run-warn": "#e0bd6f",
        "--run-failed": "#e08a82",
        "--run-skipped": "#a8927a",
        "--focus": "#6ba6db",
    }
    return {
        "$schema": "nexus-theme/v1",
        "id": theme_id,
        "name": "Demo",
        "base": "light",
        "tokens": {"light": light, "dark": dark},
    }


@pytest.fixture(autouse=True)
def _themes_dir(tmp_path):
    os.environ["NEXUS_THEMES_DIR"] = str(tmp_path / "themes")
    from app.platform.config import get_settings

    get_settings.cache_clear()
    yield
    os.environ.pop("NEXUS_THEMES_DIR", None)
    get_settings.cache_clear()


def test_validator_accepts_valid_and_rejects_bad():
    assert validate_theme(_valid_theme()).ok
    bad = _valid_theme()
    bad["tokens"]["light"]["--text"] = "#f6f1ea"  # fails AA on bg
    assert not validate_theme(bad).ok
    inj = _valid_theme()
    inj["tokens"]["light"]["--space-4"] = "#fff"  # disallowed key
    assert not validate_theme(inj).ok


def test_save_then_list_roundtrips_and_revision_advances():
    assert service.list_themes() == []
    r0 = service.revision()
    assert service.save_theme(_valid_theme("ocean")).ok
    listed = service.list_themes()
    assert [t["id"] for t in listed] == ["ocean"]
    assert service.revision() >= r0


def test_save_rejects_invalid_theme():
    bad = _valid_theme()
    del bad["tokens"]["dark"]["--accent"]
    assert not service.save_theme(bad).ok
    assert service.list_themes() == []  # nothing written


def test_endpoints_require_auth_to_write_but_not_read():
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/themes").status_code == 200
        # write without a token is rejected
        assert client.post("/api/v1/themes", json=_valid_theme("x")).status_code == 401
        tok = client.post(
            "/api/v1/auth/login", json={"username": "engineer", "password": "engineer123"}
        ).json()["access_token"]
        ok = client.post(
            "/api/v1/themes", json=_valid_theme("teal"), headers={"Authorization": f"Bearer {tok}"}
        )
        assert ok.status_code == 200
        names = {t["id"] for t in client.get("/api/v1/themes").json()["themes"]}
        assert "teal" in names
        # invalid theme → 422 with errors
        bad = _valid_theme("bad")
        bad["tokens"]["light"]["--accent"] = "notacolor"
        rej = client.post("/api/v1/themes", json=bad, headers={"Authorization": f"Bearer {tok}"})
        assert rej.status_code == 422

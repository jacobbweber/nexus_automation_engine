"""SPA deep-link fallback: when a built frontend is mounted, unknown non-API GET paths
should return index.html (so the client-side router can take over on refresh / deep link),
while real assets are served verbatim and unknown API paths still 404 as JSON."""

from __future__ import annotations

from pathlib import Path

from app.platform.app_factory import create_app
from app.platform.config import get_settings
from fastapi.testclient import TestClient


def _build_static_dir(tmp_path: Path) -> str:
    (tmp_path / "index.html").write_text("<!doctype html><title>SPA</title><div id=root>", "utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('app');", "utf-8")
    return str(tmp_path)


def test_deep_link_serves_index_html(tmp_path):
    get_settings.cache_clear()
    static = _build_static_dir(tmp_path)
    app = create_app(static_dir=static)
    try:
        with TestClient(app) as client:
            # A client-side route that has no matching file must fall back to index.html.
            resp = client.get("/catalog")
            assert resp.status_code == 200
            assert "<div id=root>" in resp.text
            # The SPA entry itself still works.
            assert client.get("/").status_code == 200
            # Real assets are served as-is (not the index fallback).
            asset = client.get("/assets/app.js")
            assert asset.status_code == 200
            assert "console.log" in asset.text
    finally:
        get_settings.cache_clear()


def test_unknown_api_path_still_404_json(tmp_path):
    get_settings.cache_clear()
    static = _build_static_dir(tmp_path)
    app = create_app(static_dir=static)
    try:
        with TestClient(app) as client:
            resp = client.get("/api/v1/does-not-exist")
            assert resp.status_code == 404
            assert resp.headers["content-type"].startswith("application/json")
    finally:
        get_settings.cache_clear()

"""In-app docs API: authored pages + generated reference (stories 29.4/29.5)."""

from __future__ import annotations

import pytest
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.automation_catalog.application.seed import seed_templates
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
    from app.contexts.determinism.application.seed import seed_pinning_rules

    seed_templates()
    seed_cmdb_schemas()
    seed_cmdb_lineage()
    seed_pinning_rules()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def test_pages_lists_authored_docs(client):
    r = client.get("/api/v1/docs-site/pages")
    assert r.status_code == 200
    paths = {p["path"] for p in r.json()}
    assert "README.md" in paths
    assert any(p.startswith("concepts/") for p in paths)
    assert any("title" in p and p["title"] for p in r.json())


def test_get_page_and_traversal_guard(client):
    ok = client.get("/api/v1/docs-site/page", params={"path": "README.md"})
    assert ok.status_code == 200 and "Nexus" in ok.json()["content"]
    # path traversal / non-md is rejected
    assert client.get("/api/v1/docs-site/page", params={"path": "../README.md"}).status_code == 400
    assert client.get("/api/v1/docs-site/page", params={"path": "nope.md"}).status_code == 404


def test_generated_reference_reflects_live_metadata(client):
    ref = client.get("/api/v1/docs-site/reference").json()
    assert ref["building_blocks"] and ref["cmdb_schemas"] and ref["pinning_rules"]
    # building blocks carry idempotency + plain summary
    assert all("idempotency" in b for b in ref["building_blocks"])
    assert any(s["type"] == "vm" for s in ref["cmdb_schemas"])
    assert any("DR-Tier" in str(r["selector"]) for r in ref["pinning_rules"])

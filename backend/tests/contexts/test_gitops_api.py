"""GitOps API: status, backup, history/diff/restore, pull-preview (story 28.5)."""

from __future__ import annotations

import shutil

import pytest
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


@pytest.fixture
def client(tmp_path):
    database.reset_for_tests()
    import os

    os.environ["NEXUS_CONFIG_REPO_DIR"] = str(tmp_path / "config-repo")
    from app.platform.config import get_settings

    get_settings.cache_clear()
    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
    from app.contexts.determinism.application.seed import seed_pinning_rules
    from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

    seed_cmdb_schemas()
    seed_cmdb_lineage()
    seed_pinning_rules()
    seed_workflow_library()
    with TestClient(create_app()) as c:
        yield c
    os.environ.pop("NEXUS_CONFIG_REPO_DIR", None)
    database.reset_for_tests()


def _tok(client, user="admin", pw="admin123"):
    return client.post("/api/v1/auth/login", json={"username": user, "password": pw}).json()[
        "access_token"
    ]


def test_status_sync_history_flow(client):
    admin = {"Authorization": f"Bearer {_tok(client)}"}
    # operator cannot back up
    op = {"Authorization": f"Bearer {_tok(client, 'operator', 'operator123')}"}
    assert client.post("/api/v1/gitops/sync", headers=op).status_code == 403
    # admin backs up
    synced = client.post("/api/v1/gitops/sync", headers=admin)
    assert (
        synced.status_code == 200 and synced.json()["available"] and synced.json()["commits"] >= 1
    )
    # history has the commit
    hist = client.get("/api/v1/gitops/history", headers=admin)
    assert hist.status_code == 200 and len(hist.json()) >= 1
    # pull-preview is in sync right after a backup
    pp = client.get("/api/v1/gitops/pull-preview", headers=admin)
    assert pp.status_code == 200 and pp.json()["in_sync"] is True


def test_restore_admin_gated(client):
    admin = {"Authorization": f"Bearer {_tok(client)}"}
    client.post("/api/v1/gitops/sync", headers=admin)
    hist = client.get("/api/v1/gitops/history", headers=admin).json()
    sha = hist[0]["sha"]
    # find a tracked path via diff/restore on a known artifact
    op = {"Authorization": f"Bearer {_tok(client, 'operator', 'operator123')}"}
    r = client.post(
        "/api/v1/gitops/restore", headers=op, json={"path": "policy/validation.json", "commit": sha}
    )
    assert r.status_code == 403
    ok = client.post(
        "/api/v1/gitops/restore",
        headers=admin,
        json={"path": "policy/validation.json", "commit": sha},
    )
    assert ok.status_code == 200 and ok.json()["content"]

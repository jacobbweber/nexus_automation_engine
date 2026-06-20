"""Canonical config serializer: stable, deterministic snapshot (story 28.1)."""

from __future__ import annotations

import json

import pytest
from app.contexts.gitops.application.serializer import snapshot
from app.platform import database


@pytest.fixture(autouse=True)
def _db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.platform.app_factory  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.automation_catalog.application.seed import seed_templates
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
    from app.contexts.determinism.application.seed import seed_pinning_rules
    from app.contexts.lifecycle_validation.application.service import seed_default_policy
    from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

    seed_templates()
    seed_cmdb_schemas()
    seed_cmdb_lineage()
    seed_pinning_rules()
    seed_workflow_library()
    seed_default_policy()
    yield
    database.reset_for_tests()


def test_snapshot_covers_artifact_types():
    snap = snapshot()
    prefixes = {p.split("/")[0] for p in snap}
    assert {"workflows", "cmdb", "pinning", "catalog", "policy"} <= prefixes
    # every value is valid JSON
    for content in snap.values():
        json.loads(content)


def test_snapshot_is_deterministic_and_strips_volatile():
    a = snapshot()
    b = snapshot()
    assert a == b  # byte-identical across calls (no volatile timestamps leak)
    # a workflow file must not contain an updated_at key
    wf_path = next(p for p in a if p.startswith("workflows/"))
    assert "updated_at" not in a[wf_path]


def test_snapshot_keys_sorted():
    snap = snapshot()
    sample = next(c for p, c in snap.items() if p.startswith("cmdb/schemas/"))
    obj = json.loads(sample)
    # top-level keys are sorted
    assert list(obj.keys()) == sorted(obj.keys())

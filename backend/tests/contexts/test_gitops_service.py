"""GitOpsService: idempotent sync, history, restore, pull-preview (stories 28.3/28.4)."""

from __future__ import annotations

import shutil

import pytest
from app.contexts.gitops.application.service import GitOpsService
from app.contexts.gitops.infrastructure.git_repo import LocalGitRepo
from app.platform import database

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


@pytest.fixture
def svc(tmp_path):
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.platform.app_factory  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
    from app.contexts.determinism.application.seed import seed_pinning_rules
    from app.contexts.lifecycle_validation.application.service import seed_default_policy
    from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

    seed_cmdb_schemas()
    seed_cmdb_lineage()
    seed_pinning_rules()
    seed_workflow_library()
    seed_default_policy()
    yield GitOpsService(repo=LocalGitRepo(tmp_path / "config-repo"))
    database.reset_for_tests()


def test_sync_commits_then_is_idempotent(svc):
    sha = svc.sync(actor="admin", reason="first")
    assert sha
    st = svc.status()
    assert st.available and st.commits == 1
    # nothing changed → no new commit
    assert svc.sync(actor="admin", reason="again") is None
    assert svc.status().commits == 1


def test_history_and_restore_after_change(svc):
    svc.sync(actor="admin", reason="baseline")
    # mutate a pinning rule → next sync commits the change
    from app.contexts.determinism.infrastructure.repository import PinningRuleRepository

    repo = PinningRuleRepository()
    rule = repo.list_all()[0]
    rule.description = "edited for test"
    repo.upsert(rule)
    sha2 = svc.sync(actor="admin", reason="rule edit")
    assert sha2
    path = f"pinning/{rule.id}.json"
    hist = svc.history(path)
    assert len(hist) >= 1
    restored = svc.restore(path, hist[-1].sha)
    assert restored  # earlier content retrievable


def test_pull_preview_in_sync_after_backup(svc):
    svc.sync(actor="admin")
    preview = svc.pull_preview()
    assert preview.in_sync and preview.differences == []
    # introduce a live change → preview shows an update to reconcile
    from app.contexts.determinism.infrastructure.repository import PinningRuleRepository

    repo = PinningRuleRepository()
    rule = repo.list_all()[0]
    rule.priority = rule.priority + 1
    repo.upsert(rule)
    preview2 = svc.pull_preview()
    assert not preview2.in_sync
    assert any(d.change == "update" for d in preview2.differences)

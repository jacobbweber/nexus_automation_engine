"""Local-git versioning adapter (story 28.2). Skips cleanly when git is unavailable."""

from __future__ import annotations

import shutil

import pytest
from app.contexts.gitops.infrastructure.git_repo import LocalGitRepo

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


@pytest.fixture
def repo(tmp_path):
    return LocalGitRepo(tmp_path / "config-repo")


def test_commit_history_and_idempotent_noop(repo):
    sha = repo.commit({"a.json": '{"x": 1}\n', "sub/b.json": "hello\n"}, "init")
    assert sha
    assert repo.status().available and repo.status().commits == 1
    # re-commit identical content → no-op (None)
    assert repo.commit({"a.json": '{"x": 1}\n', "sub/b.json": "hello\n"}, "again") is None
    assert repo.status().commits == 1
    # a real change commits
    sha2 = repo.commit({"a.json": '{"x": 2}\n', "sub/b.json": "hello\n"}, "bump")
    assert sha2 and sha2 != sha
    assert repo.status().commits == 2


def test_history_diff_restore(repo):
    repo.commit({"a.json": '{"x": 1}\n'}, "v1")
    repo.commit({"a.json": '{"x": 2}\n'}, "v2")
    hist = repo.history("a.json")
    assert [c.message for c in hist] == ["v2", "v1"]
    # restore returns the content at a prior commit (does not touch live)
    first = hist[-1].sha
    assert '"x": 1' in repo.restore("a.json", first)
    # diff between the two commits mentions the change
    d = repo.diff("a.json", first, "HEAD")
    assert "x" in d


def test_deletion_mirrors_desired_set(repo):
    repo.commit({"a.json": "1\n", "b.json": "2\n"}, "two")
    # next snapshot omits b.json → it is removed from the repo
    repo.commit({"a.json": "1\n"}, "drop-b")
    assert repo.list_paths() == ["a.json"]


def test_read_head(repo):
    repo.commit({"a.json": "live\n"}, "v1")
    assert repo.read_head("a.json") == "live\n"
    assert repo.read_head("missing.json") is None

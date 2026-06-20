"""GitOpsService — serialize + version the platform's config (backup, history, diff, restore, pull).

Local git only (ADR-0013). sync() is idempotent: it commits only when the canonical snapshot
changed. The same VersioningPort powers history/diff/restore and an (optional) pull-preview that
diffs the repo HEAD against the live config.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.contexts.gitops.application.serializer import snapshot
from app.contexts.gitops.domain.ports import Commit, RepoStatus, VersioningPort


class PullDiffItem(BaseModel):
    path: str
    change: str  # action on live to match the repo: "create" | "delete" | "update"


class PullPreview(BaseModel):
    """How the repo HEAD (desired) differs from the live config — for an optional reconcile."""

    differences: list[PullDiffItem]
    in_sync: bool


def _repo() -> VersioningPort:
    from app.contexts.gitops.infrastructure.git_repo import LocalGitRepo
    from app.platform.config import get_settings

    return LocalGitRepo(get_settings().config_repo_dir)


class GitOpsService:
    def __init__(self, repo: VersioningPort | None = None) -> None:
        self.repo = repo or _repo()

    def status(self) -> RepoStatus:
        return self.repo.status()

    def sync(self, actor: str = "system", reason: str = "scheduled backup") -> str | None:
        """Serialize the live config and commit if anything changed. Returns the sha or None."""
        files = snapshot()
        message = f"config backup: {reason}\n\nactor: {actor}\nartifacts: {len(files)}"
        return self.repo.commit(files, message)

    def history(self, path: str | None = None, limit: int = 50) -> list[Commit]:
        return self.repo.history(path, limit)

    def diff(self, path: str, a: str, b: str = "HEAD") -> str:
        return self.repo.diff(path, a, b)

    def restore(self, path: str, commit: str) -> str:
        return self.repo.restore(path, commit)

    def pull_preview(self) -> PullPreview:
        """Diff the committed config (repo HEAD = desired) against the live snapshot."""
        live = snapshot()
        tracked = set(self.repo.list_paths())
        diffs: list[PullDiffItem] = []
        for path in sorted(tracked | set(live)):
            in_repo = path in tracked
            in_live = path in live
            if in_repo and not in_live:
                diffs.append(PullDiffItem(path=path, change="create"))  # repo has it, live lacks it
            elif in_live and not in_repo:
                diffs.append(PullDiffItem(path=path, change="delete"))  # live has it, repo lacks it
            elif self.repo.read_head(path) != live.get(path):
                diffs.append(PullDiffItem(path=path, change="update"))
        return PullPreview(differences=diffs, in_sync=not diffs)

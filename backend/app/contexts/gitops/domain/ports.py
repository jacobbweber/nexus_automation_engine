"""VersioningPort — the interface the GitOps service depends on (Git adapter implements it)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class Commit(BaseModel):
    sha: str
    message: str
    date: str
    author: str


class RepoStatus(BaseModel):
    available: bool  # is a versioning backend usable (git present + repo initialised)?
    path: str = ""
    head: str | None = None
    dirty: bool = False
    commits: int = 0


@runtime_checkable
class VersioningPort(Protocol):
    def available(self) -> bool: ...

    def status(self) -> RepoStatus: ...

    def commit(self, files: dict[str, str], message: str) -> str | None:
        """Write files (path->content), stage, and commit. Returns the sha, or None if no change."""
        ...

    def history(self, path: str | None = None, limit: int = 50) -> list[Commit]: ...

    def diff(self, path: str, a: str, b: str = "HEAD") -> str: ...

    def restore(self, path: str, commit: str) -> str:
        """Return the content of ``path`` at ``commit`` (does not write to live state)."""
        ...

    def read_head(self, path: str) -> str | None:
        """Current committed content of ``path`` at HEAD (for pull/diff), or None if absent."""
        ...

    def list_paths(self) -> list[str]:
        """All tracked file paths at HEAD."""
        ...

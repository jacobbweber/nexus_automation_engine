"""Local-git versioning adapter (official git via subprocess).

Guardrail: LOCAL only — no remote, no paid services. Commits carry an audit message (actor/what),
never secrets. Degrades gracefully when the git binary is absent (``available()`` is False) so the
rest of the platform runs unaffected.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.contexts.gitops.domain.ports import Commit, RepoStatus

# Fixed local identity so commits work on CI runners without a configured git user.
_GIT_ID = ["-c", "user.email=nexus@local", "-c", "user.name=Nexus"]


class LocalGitRepo:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    # ---- helpers ----

    def _git_bin(self) -> str | None:
        return shutil.which("git")

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        # core.autocrlf=false so \n content stays \n (no spurious "dirty" / non-idempotent commits).
        return subprocess.run(  # noqa: S603 - args are literal git subcommands, root is ours
            [self._git_bin() or "git", "-c", "core.autocrlf=false", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",  # decode git output as UTF-8 (not the Windows locale codec)
            check=check,
        )

    def available(self) -> bool:
        return self._git_bin() is not None

    def _ensure_repo(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not (self.root / ".git").exists():
            subprocess.run(  # noqa: S603
                [self._git_bin() or "git", "init", "-q", str(self.root)],
                capture_output=True,
                text=True,
                check=True,
            )

    # ---- port ----

    def status(self) -> RepoStatus:
        if not self.available() or not (self.root / ".git").exists():
            return RepoStatus(available=False, path=str(self.root))
        head = self._run("rev-parse", "--short", "HEAD", check=False)
        dirty = bool(self._run("status", "--porcelain", check=False).stdout.strip())
        count = self._run("rev-list", "--count", "HEAD", check=False).stdout.strip()
        return RepoStatus(
            available=True,
            path=str(self.root),
            head=head.stdout.strip() or None,
            dirty=dirty,
            commits=int(count) if count.isdigit() else 0,
        )

    def commit(self, files: dict[str, str], message: str) -> str | None:
        if not self.available():
            return None
        self._ensure_repo()
        # mirror the desired file set: write provided files, delete tracked files no longer present
        for rel, content in files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            # newline="" so \n is written verbatim (no Windows \r\n translation), keeping committed
            # content byte-identical to the canonical snapshot.
            p.write_text(content, encoding="utf-8", newline="")
        desired = set(files)
        for tracked in self.list_paths():
            if tracked not in desired:
                tp = self.root / tracked
                if tp.exists():
                    tp.unlink()
        self._run("add", "-A")
        if not self._run("status", "--porcelain", check=False).stdout.strip():
            return None  # nothing changed — idempotent no-op
        self._run(*_GIT_ID, "commit", "-q", "-m", message)
        return self._run("rev-parse", "--short", "HEAD").stdout.strip()

    def history(self, path: str | None = None, limit: int = 50) -> list[Commit]:
        if not self.available() or not (self.root / ".git").exists():
            return []
        fmt = "%h%x1f%s%x1f%cI%x1f%an"
        args = ["log", f"-{limit}", f"--pretty=format:{fmt}"]
        if path:
            args += ["--", path]
        out = self._run(*args, check=False).stdout
        commits: list[Commit] = []
        for line in out.splitlines():
            parts = line.split("\x1f")
            if len(parts) == 4:
                commits.append(
                    Commit(sha=parts[0], message=parts[1], date=parts[2], author=parts[3])
                )
        return commits

    def diff(self, path: str, a: str, b: str = "HEAD") -> str:
        if not self.available():
            return ""
        return self._run("diff", a, b, "--", path, check=False).stdout

    def restore(self, path: str, commit: str) -> str:
        if not self.available():
            return ""
        return self._run("show", f"{commit}:{path}", check=False).stdout

    def read_head(self, path: str) -> str | None:
        if not self.available():
            return None
        res = self._run("show", f"HEAD:{path}", check=False)
        # subprocess text mode normalizes \r\n→\n; keep it that way to match the canonical snapshot.
        return res.stdout.replace("\r\n", "\n") if res.returncode == 0 else None

    def list_paths(self) -> list[str]:
        if not self.available() or not (self.root / ".git").exists():
            return []
        out = self._run("ls-files", check=False).stdout
        return [line.strip() for line in out.splitlines() if line.strip()]

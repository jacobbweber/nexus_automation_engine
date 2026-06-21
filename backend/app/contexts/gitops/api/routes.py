"""GitOps routes: config-as-code status, backup, history/diff/restore, and pull-preview."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.contexts.gitops.application.service import GitOpsService, PullPreview
from app.contexts.gitops.domain.ports import Commit, RepoStatus
from app.contexts.identity_access.api.deps import get_current_user, require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext

router = APIRouter(prefix="/gitops", tags=["gitops"])


@router.get("/status", response_model=RepoStatus)
def status(_user: UserContext = Depends(get_current_user)) -> RepoStatus:
    return GitOpsService().status()


@router.post("/sync", response_model=RepoStatus)
def sync(admin: UserContext = Depends(require_role(GlobalRole.ADMIN))) -> RepoStatus:
    """Back up the current config to the local repo now (commits only if changed)."""
    svc = GitOpsService()
    svc.sync(actor=admin.username, reason="manual backup")
    return svc.status()


@router.get("/history", response_model=list[Commit])
def history(
    path: str | None = None, _user: UserContext = Depends(get_current_user)
) -> list[Commit]:
    return GitOpsService().history(path)


@router.get("/diff")
def diff(
    path: str, a: str, b: str = "HEAD", _user: UserContext = Depends(get_current_user)
) -> dict[str, str]:
    return {"diff": GitOpsService().diff(path, a, b)}


class RestoreRequest(BaseModel):
    path: str
    commit: str


@router.post("/restore")
def restore(
    body: RestoreRequest, _admin: UserContext = Depends(require_role(GlobalRole.ADMIN))
) -> dict[str, str]:
    """Return the content of an artifact at a prior commit (does not overwrite live state)."""
    return {"content": GitOpsService().restore(body.path, body.commit)}


@router.get("/pull-preview", response_model=PullPreview)
def pull_preview(_user: UserContext = Depends(get_current_user)) -> PullPreview:
    return GitOpsService().pull_preview()

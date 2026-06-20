"""Compliance posture routes: latest/history snapshots + admin-triggered sweep."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contexts.compliance.application.service import ComplianceSweepService
from app.contexts.compliance.domain.models import PostureSnapshot
from app.contexts.identity_access.api.deps import require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/posture", response_model=PostureSnapshot | None)
def latest_posture() -> PostureSnapshot | None:
    return ComplianceSweepService().latest()


@router.get("/posture/history", response_model=list[PostureSnapshot])
def posture_history() -> list[PostureSnapshot]:
    return ComplianceSweepService().history()


@router.post("/sweep", response_model=PostureSnapshot)
def run_sweep(_admin: UserContext = Depends(require_role(GlobalRole.ADMIN))) -> PostureSnapshot:
    """Trigger a compliance sweep now (also runs on the scheduler cadence)."""
    return ComplianceSweepService().run_sweep()

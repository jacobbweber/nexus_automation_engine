"""Review routes: build a multi-audience change review packet for a workflow."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contexts.identity_access.api.deps import get_current_user
from app.contexts.identity_access.domain.models import UserContext
from app.contexts.review.application.service import ReviewService
from app.contexts.review.domain.packet import ReviewPacket

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/packet/{workflow_id}", response_model=ReviewPacket)
def workflow_packet(
    workflow_id: str, _user: UserContext = Depends(get_current_user)
) -> ReviewPacket:
    """The technical / non-technical / executive review packet for a workflow."""
    return ReviewService().build_for_workflow(workflow_id)

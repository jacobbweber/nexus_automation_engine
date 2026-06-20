"""Review routes: build a multi-audience change review packet for a workflow."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.contexts.identity_access.api.deps import get_current_user
from app.contexts.identity_access.domain.models import UserContext
from app.contexts.review.application.service import ReviewService
from app.contexts.review.domain.approval import ApprovalDecision, ApprovalRequest
from app.contexts.review.domain.packet import ReviewPacket

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/packet/{workflow_id}", response_model=ReviewPacket)
def workflow_packet(
    workflow_id: str, _user: UserContext = Depends(get_current_user)
) -> ReviewPacket:
    """The technical / non-technical / executive review packet for a workflow."""
    return ReviewService().build_for_workflow(workflow_id)


@router.get("/approvals", response_model=list[ApprovalRequest])
def pending_approvals(_user: UserContext = Depends(get_current_user)) -> list[ApprovalRequest]:
    return ReviewService().pending()


@router.get("/approvals/{request_id}", response_model=ApprovalRequest)
def get_approval(
    request_id: str, _user: UserContext = Depends(get_current_user)
) -> ApprovalRequest:
    return ReviewService().get_request(request_id)


class CreateApprovalRequest(BaseModel):
    workflow_id: str
    inputs: dict = {}


@router.post("/approvals", response_model=ApprovalRequest)
def create_approval(
    body: CreateApprovalRequest, user: UserContext = Depends(get_current_user)
) -> ApprovalRequest:
    return ReviewService().request_approval(
        body.workflow_id, body.inputs, requested_by=user.username
    )


class CiChangeRequest(BaseModel):
    ci: dict


@router.post("/ci-change", response_model=ApprovalRequest)
def request_ci_change(
    body: CiChangeRequest, user: UserContext = Depends(get_current_user)
) -> ApprovalRequest:
    """Propose a CI add/modify — health-checked (M24), gated on approval, and pinning-reconciled."""
    req = ReviewService().request_ci_change(body.ci, requested_by=user.username)
    # Trigger hook (M27.4): on-change pinning rules may enforce a guaranteed workflow for this CI.
    from app.contexts.determinism.application.service import DeterminismService

    DeterminismService().on_ci_change(body.ci)
    return req


class DecisionRequest(BaseModel):
    decision: ApprovalDecision
    comment: str = ""


@router.post("/approvals/{request_id}/decision", response_model=ApprovalRequest)
def decide_approval(
    request_id: str, body: DecisionRequest, user: UserContext = Depends(get_current_user)
) -> ApprovalRequest:
    return ReviewService().decide(request_id, body.decision, user.username, body.comment)

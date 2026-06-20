"""ReviewService — review packets, run-level approval requests, and the run gate."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.contexts.review.domain.approval import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
)
from app.contexts.review.domain.classification import ReviewPolicy
from app.contexts.review.domain.packet import BlockInfo, ReviewPacket, build_packet
from app.contexts.review.infrastructure.repository import ApprovalRepository
from app.shared_kernel.errors import ConflictError, NotFoundError
from app.shared_kernel.ids import new_id


class ReviewService:
    def __init__(self, approvals: ApprovalRepository | None = None) -> None:
        self.approvals = approvals or ApprovalRepository()

    def _block_lookup(self) -> dict[tuple[str, str], BlockInfo]:
        from app.contexts.automation_catalog.application.service import CatalogService

        lookup: dict[tuple[str, str], BlockInfo] = {}
        for t in CatalogService().list_all():
            ps = t.plain_summary
            lookup[(str(t.connector), t.action)] = BlockInfo(
                plain_action=ps.action if ps else "",
                plain_outcome=ps.outcome if ps else "",
                rollback=ps.rollback if ps else "",
                risk=str(t.risk),
                idempotency=t.idempotency,
            )
        return lookup

    def build_for_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, Any] | None = None,
        policy: ReviewPolicy | None = None,
    ) -> ReviewPacket:
        from app.contexts.orchestration_canvas.application.service import CanvasService

        wf = CanvasService().get_workflow(workflow_id)
        nodes = [
            {"id": n.id, "type": str(n.type), "data": n.data, "name": n.data.get("name", "")}
            for n in wf.graph.nodes
        ]
        return build_packet(
            workflow_id=wf.id,
            workflow_name=wf.name,
            nodes=nodes,
            inputs=inputs or {},
            block_lookup=self._block_lookup(),
            policy=policy,
        )

    # ---- approval requests ----

    def request_approval(
        self, workflow_id: str, inputs: dict[str, Any] | None = None, requested_by: str = ""
    ) -> ApprovalRequest:
        """Build the packet and open a pending approval request (reusing any open one)."""
        packet = self.build_for_workflow(workflow_id, inputs)
        existing = [
            r
            for r in self.approvals.find_for_source("run", workflow_id)
            if r.status == ApprovalStatus.PENDING
        ]
        if existing:
            return existing[0]
        req = ApprovalRequest(
            id=new_id("appr"),
            source_type="run",
            source_id=workflow_id,
            title=f"Run approval: {packet.workflow_name}",
            change_class=str(packet.change_class),
            required_level=str(packet.required_level),
            packet=packet,
            requested_by=requested_by,
        )
        return self.approvals.save(req)

    def decide(
        self, request_id: str, decision: ApprovalDecision, decided_by: str, comment: str = ""
    ) -> ApprovalRequest:
        req = self.approvals.get(request_id)
        if req is None:
            raise NotFoundError(f"Approval request {request_id} not found")
        req.status = {
            ApprovalDecision.APPROVE: ApprovalStatus.APPROVED,
            ApprovalDecision.REJECT: ApprovalStatus.REJECTED,
            ApprovalDecision.REQUEST_CHANGES: ApprovalStatus.CHANGES_REQUESTED,
        }[decision]
        req.decided_by = decided_by
        req.comment = comment
        req.decided_at = datetime.now(UTC)
        return self.approvals.save(req)

    def pending(self) -> list[ApprovalRequest]:
        return self.approvals.list_by_status(ApprovalStatus.PENDING)

    def get_request(self, request_id: str) -> ApprovalRequest:
        req = self.approvals.get(request_id)
        if req is None:
            raise NotFoundError(f"Approval request {request_id} not found")
        return req

    def has_approval(self, workflow_id: str) -> bool:
        return any(
            r.status == ApprovalStatus.APPROVED
            for r in self.approvals.find_for_source("run", workflow_id)
        )

    def enforce_run_allowed(self, workflow_id: str) -> None:
        """Gate a run: if the workflow's packet requires approval and none is approved, block it."""
        packet = self.build_for_workflow(workflow_id)
        if packet.requires_approval and not self.has_approval(workflow_id):
            raise ConflictError(
                f"This run requires {packet.required_level} approval "
                f"({packet.change_class}). Submit it for review in the approvals queue."
            )

"""ReviewService — assemble a Change Review Packet for a workflow from catalog plain summaries."""

from __future__ import annotations

from typing import Any

from app.contexts.review.domain.classification import ReviewPolicy
from app.contexts.review.domain.packet import BlockInfo, ReviewPacket, build_packet


class ReviewService:
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

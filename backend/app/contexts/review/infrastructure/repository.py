"""Approval request repository."""

from __future__ import annotations

from app.contexts.review.domain.approval import ApprovalRequest, ApprovalStatus
from app.contexts.review.domain.packet import ReviewPacket
from app.contexts.review.infrastructure.orm import ApprovalRequestRow
from app.platform.database import get_sessionmaker


def _to_req(row: ApprovalRequestRow) -> ApprovalRequest:
    return ApprovalRequest(
        id=row.id,
        source_type=row.source_type,
        source_id=row.source_id,
        title=row.title,
        change_class=row.change_class,
        required_level=row.required_level,
        status=ApprovalStatus(row.status),
        packet=ReviewPacket.model_validate_json(row.packet_json) if row.packet_json else None,
        requested_by=row.requested_by,
        decided_by=row.decided_by,
        comment=row.comment,
        created_at=row.created_at,
        decided_at=row.decided_at,
    )


class ApprovalRepository:
    def save(self, req: ApprovalRequest) -> ApprovalRequest:
        with get_sessionmaker()() as s:
            row = s.get(ApprovalRequestRow, req.id) or ApprovalRequestRow(id=req.id)
            row.source_type = req.source_type
            row.source_id = req.source_id
            row.title = req.title
            row.change_class = req.change_class
            row.required_level = req.required_level
            row.status = str(req.status)
            row.packet_json = req.packet.model_dump_json() if req.packet else ""
            row.requested_by = req.requested_by
            row.decided_by = req.decided_by
            row.comment = req.comment
            row.created_at = req.created_at
            row.decided_at = req.decided_at
            s.add(row)
            s.commit()
        return req

    def get(self, req_id: str) -> ApprovalRequest | None:
        with get_sessionmaker()() as s:
            row = s.get(ApprovalRequestRow, req_id)
            return _to_req(row) if row else None

    def list_by_status(self, status: ApprovalStatus | None = None) -> list[ApprovalRequest]:
        with get_sessionmaker()() as s:
            q = s.query(ApprovalRequestRow).order_by(ApprovalRequestRow.created_at.desc())
            if status is not None:
                q = q.filter(ApprovalRequestRow.status == str(status))
            return [_to_req(r) for r in q.all()]

    def find_for_source(self, source_type: str, source_id: str) -> list[ApprovalRequest]:
        with get_sessionmaker()() as s:
            rows = (
                s.query(ApprovalRequestRow)
                .filter(
                    ApprovalRequestRow.source_type == source_type,
                    ApprovalRequestRow.source_id == source_id,
                )
                .order_by(ApprovalRequestRow.created_at.desc())
                .all()
            )
            return [_to_req(r) for r in rows]

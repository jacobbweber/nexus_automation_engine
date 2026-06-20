"""Posture snapshot repository."""

from __future__ import annotations

import json

from app.contexts.compliance.domain.models import DriftedItem, PostureSnapshot
from app.contexts.compliance.infrastructure.orm import PostureSnapshotRow
from app.platform.database import get_sessionmaker


def _to_snapshot(row: PostureSnapshotRow) -> PostureSnapshot:
    return PostureSnapshot(
        id=row.id,
        created_at=row.created_at,
        evaluated=row.evaluated,
        compliant=row.compliant,
        drifted=row.drifted,
        drift_count=row.drift_count,
        top_drifted=[DriftedItem(**d) for d in json.loads(row.top_drifted_json or "[]")],
    )


class PostureRepository:
    def save(self, snap: PostureSnapshot) -> PostureSnapshot:
        with get_sessionmaker()() as s:
            row = s.get(PostureSnapshotRow, snap.id) or PostureSnapshotRow(id=snap.id)
            row.created_at = snap.created_at
            row.evaluated = snap.evaluated
            row.compliant = snap.compliant
            row.drifted = snap.drifted
            row.drift_count = snap.drift_count
            row.top_drifted_json = json.dumps([d.model_dump() for d in snap.top_drifted])
            s.add(row)
            s.commit()
        return snap

    def latest(self) -> PostureSnapshot | None:
        with get_sessionmaker()() as s:
            row = s.query(PostureSnapshotRow).order_by(PostureSnapshotRow.created_at.desc()).first()
            return _to_snapshot(row) if row else None

    def history(self, limit: int = 30) -> list[PostureSnapshot]:
        with get_sessionmaker()() as s:
            rows = (
                s.query(PostureSnapshotRow)
                .order_by(PostureSnapshotRow.created_at.desc())
                .limit(limit)
                .all()
            )
            return [_to_snapshot(r) for r in rows]

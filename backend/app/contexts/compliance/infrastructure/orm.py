"""ORM row for compliance posture snapshots (top-drifted stored as JSON)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class PostureSnapshotRow(Base):
    __tablename__ = "compliance_posture"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    evaluated: Mapped[int] = mapped_column(Integer, default=0)
    compliant: Mapped[int] = mapped_column(Integer, default=0)
    drifted: Mapped[int] = mapped_column(Integer, default=0)
    drift_count: Mapped[int] = mapped_column(Integer, default=0)
    top_drifted_json: Mapped[str] = mapped_column(Text, default="[]")

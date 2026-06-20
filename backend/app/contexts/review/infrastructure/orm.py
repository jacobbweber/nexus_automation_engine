"""ORM row for approval requests (packet snapshot stored as JSON)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class ApprovalRequestRow(Base):
    __tablename__ = "review_approval"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_type: Mapped[str] = mapped_column(String, index=True)
    source_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String, default="")
    change_class: Mapped[str] = mapped_column(String, default="normal")
    required_level: Mapped[str] = mapped_column(String, default="team_lead")
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    packet_json: Mapped[str] = mapped_column(Text, default="")
    requested_by: Mapped[str] = mapped_column(String, default="")
    decided_by: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

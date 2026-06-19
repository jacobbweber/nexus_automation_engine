"""ORM row for schedules."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class ScheduleRow(Base):
    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    workflow_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    inputs_json: Mapped[str] = mapped_column(Text, default="{}")
    kind: Mapped[str] = mapped_column(String, default="interval")
    interval_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    daily_time: Mapped[str] = mapped_column(String, default="02:00")
    window_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

"""SQLAlchemy ORM rows for jobs and their log streams."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.platform.database import Base


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    connector: Mapped[str] = mapped_column(String, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    params_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    check_mode: Mapped[bool] = mapped_column(default=False)
    diff_mode: Mapped[bool] = mapped_column(default=False)
    initiated_by: Mapped[str] = mapped_column(String, nullable=False, index=True)
    asset_group: Mapped[str | None] = mapped_column(String, nullable=True)
    change_number: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    workflow_node_id: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    logs: Mapped[list[JobLogRow]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="JobLogRow.sequence"
    )


class JobLogRow(Base):
    __tablename__ = "job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    stream: Mapped[str] = mapped_column(String, default="stdout")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    job: Mapped[JobRow] = relationship(back_populates="logs")

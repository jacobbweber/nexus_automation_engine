"""Compliance posture domain models."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, computed_field


class DriftedItem(BaseModel):
    target: str
    drift_count: int


class PostureSnapshot(BaseModel):
    """A point-in-time picture of the estate's compliance, from one sweep."""

    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evaluated: int = 0  # workflows evaluated
    compliant: int = 0
    drifted: int = 0
    drift_count: int = 0  # total drifted fields across all
    top_drifted: list[DriftedItem] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]  # serialized in API responses
    @property
    def compliant_pct(self) -> int:
        return round(100 * self.compliant / self.evaluated) if self.evaluated else 100

"""Incident kanban routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.contexts.incident_management.application.service import IncidentService
from app.contexts.incident_management.domain.models import Incident, IncidentStatus

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/board", response_model=dict[str, list[Incident]])
def board() -> dict[str, list[Incident]]:
    return IncidentService().board()


@router.get("", response_model=list[Incident])
def list_incidents() -> list[Incident]:
    return IncidentService().list_all()


@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str) -> Incident:
    return IncidentService().get(incident_id)


class MoveRequest(BaseModel):
    status: IncidentStatus
    assigned_to: str | None = None


@router.post("/{incident_id}/move", response_model=Incident)
def move_incident(incident_id: str, body: MoveRequest) -> Incident:
    return IncidentService().move(incident_id, body.status, body.assigned_to)


class RemediateResponse(BaseModel):
    workflow_id: str


@router.post("/{incident_id}/remediate", response_model=RemediateResponse)
def remediate(incident_id: str) -> RemediateResponse:
    return RemediateResponse(workflow_id=IncidentService().remediate(incident_id))

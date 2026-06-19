"""Change management routes: templates, policies, and records."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.contexts.change_management.application.service import ChangeService
from app.contexts.change_management.domain.models import (
    ChangeControlPolicy,
    ChangeRecord,
    ChangeTemplate,
    Risk,
)
from app.contexts.identity_access.api.deps import require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.shared_kernel.ids import new_id

router = APIRouter(prefix="/change", tags=["change-management"])


@router.get("/templates", response_model=list[ChangeTemplate])
def list_templates() -> list[ChangeTemplate]:
    return ChangeService().list_templates()


class TemplateDraft(BaseModel):
    name: str
    short_description: str = ""
    assignment_group: str = "Automation"
    category: str = "Standard"
    risk: Risk = Risk.LOW
    impact: str = "low"
    cab_required: bool = False


@router.post("/templates", response_model=ChangeTemplate)
def create_template(
    draft: TemplateDraft, _eng: UserContext = Depends(require_role(GlobalRole.ENGINEER))
) -> ChangeTemplate:
    return ChangeService().create_template(
        ChangeTemplate(id=new_id("chgtpl"), **draft.model_dump())
    )


class PolicyRequest(BaseModel):
    resource_type: str
    resource_id: str
    auto_change_control: bool = True
    change_template_id: str | None = None
    require_approved_change: bool = False


@router.put("/policies", response_model=ChangeControlPolicy)
def set_policy(
    body: PolicyRequest, _eng: UserContext = Depends(require_role(GlobalRole.ENGINEER))
) -> ChangeControlPolicy:
    return ChangeService().set_policy(ChangeControlPolicy(id=new_id("chgpol"), **body.model_dump()))


@router.get("/policies/{resource_type}/{resource_id}", response_model=ChangeControlPolicy | None)
def get_policy(resource_type: str, resource_id: str) -> ChangeControlPolicy | None:
    return ChangeService().get_policy(resource_type, resource_id)


@router.get("/records", response_model=list[ChangeRecord])
def list_records() -> list[ChangeRecord]:
    return ChangeService().list_records()


@router.get("/records/{number}", response_model=ChangeRecord)
def get_record(number: str) -> ChangeRecord:
    return ChangeService().get_record(number)

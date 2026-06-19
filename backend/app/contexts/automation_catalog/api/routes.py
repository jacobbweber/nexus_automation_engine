"""Catalog routes: browse approved building blocks, author/approve, execute-from-template."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.contexts.automation_catalog.application.service import CatalogService
from app.contexts.automation_catalog.domain.models import (
    ApprovalState,
    Template,
    TemplateDraft,
)
from app.contexts.execution_engine.domain.models import JobStatus
from app.contexts.identity_access.api.deps import get_current_user, require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/templates", response_model=list[Template])
def list_templates(
    state: ApprovalState | None = None,
    domain: str | None = None,
    vendor: str | None = None,
    search: str | None = None,
) -> list[Template]:
    # Default view = approved building blocks (what operators run).
    return CatalogService().list(
        approval_state=state or ApprovalState.APPROVED, domain=domain, vendor=vendor, search=search
    )


@router.get("/facets")
def catalog_facets() -> dict[str, dict[str, int]]:
    return CatalogService().facets()


@router.get("/templates/{template_id}", response_model=Template)
def get_template(template_id: str) -> Template:
    return CatalogService().get(template_id)


@router.post("/templates", response_model=Template)
def create_template(
    draft: TemplateDraft,
    user: UserContext = Depends(require_role(GlobalRole.ENGINEER)),
) -> Template:
    return CatalogService().create(draft, owner=user.username)


@router.post("/templates/{template_id}/approve", response_model=Template)
def approve_template(
    template_id: str,
    _user: UserContext = Depends(require_role(GlobalRole.ENGINEER)),
) -> Template:
    return CatalogService().approve(template_id)


@router.post("/templates/{template_id}/retire", response_model=Template)
def retire_template(
    template_id: str,
    _user: UserContext = Depends(require_role(GlobalRole.ENGINEER)),
) -> Template:
    return CatalogService().retire(template_id)


class ExecuteTemplateRequest(BaseModel):
    survey_answers: dict[str, object] = Field(default_factory=dict)
    check_mode: bool = False
    diff_mode: bool = False


class ExecuteTemplateResponse(BaseModel):
    job_id: str
    status: JobStatus


@router.post("/templates/{template_id}/execute", response_model=ExecuteTemplateResponse)
async def execute_template(
    template_id: str,
    body: ExecuteTemplateRequest,
    user: UserContext = Depends(get_current_user),
) -> ExecuteTemplateResponse:
    job = await CatalogService().execute(
        template_id,
        user=user,
        survey_answers=body.survey_answers,
        check_mode=body.check_mode,
        diff_mode=body.diff_mode,
    )
    return ExecuteTemplateResponse(job_id=job.id, status=job.status)

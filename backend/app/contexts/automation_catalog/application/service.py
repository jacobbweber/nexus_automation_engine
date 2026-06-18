"""Catalog service: author/approve building blocks and execute them as governed jobs."""

from __future__ import annotations

from datetime import UTC, datetime

from app.contexts.automation_catalog.domain.models import (
    ApprovalState,
    Template,
    TemplateDraft,
)
from app.contexts.automation_catalog.infrastructure.repository import TemplateRepository
from app.contexts.execution_engine.application.service import ExecutionService
from app.contexts.execution_engine.domain.models import Job, JobSubmission
from app.contexts.identity_access.domain.entitlements import has_capability
from app.contexts.identity_access.domain.models import Capability, UserContext
from app.shared_kernel.errors import ConflictError, EntitlementError, NotFoundError
from app.shared_kernel.ids import new_id


def _now() -> datetime:
    return datetime.now(UTC)


class CatalogService:
    def __init__(
        self,
        repository: TemplateRepository | None = None,
        execution: ExecutionService | None = None,
    ) -> None:
        self.repo = repository or TemplateRepository()
        self.execution = execution or ExecutionService()

    def create(self, draft: TemplateDraft, *, owner: str) -> Template:
        now = _now()
        template = Template(
            id=new_id("tpl"),
            owner=owner,
            approval_state=ApprovalState.DRAFT,
            created_at=now,
            updated_at=now,
            **draft.model_dump(),
        )
        return self.repo.upsert(template)

    def get(self, template_id: str) -> Template:
        template = self.repo.get(template_id)
        if template is None:
            raise NotFoundError(f"Template {template_id} not found")
        return template

    def list(self, *, approval_state: ApprovalState | None = None) -> list[Template]:
        return self.repo.list(approval_state=approval_state)

    def submit_for_approval(self, template_id: str) -> Template:
        self.get(template_id)
        self.repo.set_state(template_id, ApprovalState.PENDING, updated_at=_now())
        return self.get(template_id)

    def approve(self, template_id: str) -> Template:
        self.get(template_id)
        self.repo.set_state(template_id, ApprovalState.APPROVED, updated_at=_now())
        return self.get(template_id)

    def retire(self, template_id: str) -> Template:
        self.get(template_id)
        self.repo.set_state(template_id, ApprovalState.RETIRED, updated_at=_now())
        return self.get(template_id)

    async def execute(
        self,
        template_id: str,
        *,
        user: UserContext,
        survey_answers: dict[str, object],
        check_mode: bool = False,
        diff_mode: bool = False,
    ) -> Job:
        template = self.get(template_id)
        if template.approval_state != ApprovalState.APPROVED:
            raise ConflictError("Template is not approved for execution")

        live = not check_mode
        capability = Capability.EXECUTE_LIVE if live else Capability.EXECUTE_CHECK
        if not has_capability(user, capability):
            raise EntitlementError("Not entitled to execute this template in the requested mode")

        params = {**template.default_params, **survey_answers}
        submission = JobSubmission(
            name=template.name,
            connector=template.connector,
            action=template.action,
            params=params,
            check_mode=check_mode,
            diff_mode=diff_mode,
            initiated_by=user.username,
        )
        return await self.execution.submit_and_run(submission)

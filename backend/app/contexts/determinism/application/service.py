"""DeterminismService — rules CRUD, reconciliation, and coverage over the live CMDB."""

from __future__ import annotations

from app.contexts.determinism.domain.models import PinningRule, Trigger, validate_rule
from app.contexts.determinism.domain.reconcile import (
    Coverage,
    PinnedAction,
    compute_coverage,
    plan_actions,
)
from app.contexts.determinism.infrastructure.repository import PinningRuleRepository
from app.shared_kernel.errors import NotFoundError, ValidationError


class DeterminismService:
    def __init__(self, repository: PinningRuleRepository | None = None) -> None:
        self.repo = repository or PinningRuleRepository()

    # ---- rules CRUD ----

    def list_rules(self) -> list[PinningRule]:
        return self.repo.list_all()

    def get_rule(self, rule_id: str) -> PinningRule:
        rule = self.repo.get(rule_id)
        if rule is None:
            raise NotFoundError(f"Pinning rule {rule_id} not found")
        return rule

    def upsert_rule(self, rule: PinningRule) -> PinningRule:
        errors = validate_rule(rule)
        if errors:
            raise ValidationError("; ".join(errors))
        return self.repo.upsert(rule)

    def delete_rule(self, rule_id: str) -> bool:
        return self.repo.delete(rule_id)

    # ---- reconciliation + coverage (read the live CMDB) ----

    async def reconcile(self, trigger: Trigger | None = None) -> list[PinnedAction]:
        from app.contexts.determinism.infrastructure.ci_source import all_cis

        return plan_actions(self.repo.list_all(), await all_cis(), trigger)

    def on_ci_change(self, ci: dict[str, object]) -> list[PinnedAction]:
        """Trigger hook: plan on-change actions for one CI and open review approvals for enforce
        rules whose guaranteed workflow resolves. assert/gate are surfaced in the returned plan."""
        from app.contexts.determinism.domain.models import Enforcement
        from app.contexts.orchestration_canvas.application.service import CanvasService
        from app.contexts.review.application.service import ReviewService

        plan = plan_actions(self.repo.list_all(), [ci], Trigger.ON_CHANGE)
        by_name = {w.name: w.id for w in CanvasService().list_workflows()}
        review = ReviewService()
        for action in plan:
            if action.enforcement == Enforcement.ENFORCE:
                wf_id = by_name.get(action.workflow)
                if wf_id:
                    review.request_approval(wf_id, requested_by="pinning-reconciler")
        return plan

    async def coverage(self) -> Coverage:
        from app.contexts.connectors.application.services import evaluate_compliance
        from app.contexts.connectors.domain.models import ConnectorKind, ExecutionRequest
        from app.contexts.determinism.infrastructure.ci_source import all_cis
        from app.contexts.orchestration_canvas.application.service import CanvasService

        cis = await all_cis()
        workflows = CanvasService().list_workflows()
        names = {w.name for w in workflows} | {w.id for w in workflows}

        def workflow_exists(ref: str) -> bool:
            return ref in names

        def drift_of(ci: dict[str, object], rule: PinningRule) -> str:
            # assert the CI's desired state (deterministic drift seeded by target + rule)
            req = ExecutionRequest(
                kind=ConnectorKind.SERVICENOW,
                action=f"reconcile_state_{rule.id}",
                params={"target": str(ci.get("name", ""))},
            )
            return evaluate_compliance(req).status

        return compute_coverage(
            self.repo.list_all(), cis, workflow_exists=workflow_exists, drift_of=drift_of
        )

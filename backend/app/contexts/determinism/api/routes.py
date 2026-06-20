"""Determinism routes: pinning rules CRUD (admin), coverage, and on-demand reconcile."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contexts.determinism.application.service import DeterminismService
from app.contexts.determinism.domain.models import PinningRule
from app.contexts.determinism.domain.reconcile import Coverage, PinnedAction
from app.contexts.identity_access.api.deps import get_current_user, require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext

router = APIRouter(prefix="/determinism", tags=["determinism"])


@router.get("/rules", response_model=list[PinningRule])
def list_rules(_user: UserContext = Depends(get_current_user)) -> list[PinningRule]:
    return DeterminismService().list_rules()


@router.get("/rules/{rule_id}", response_model=PinningRule)
def get_rule(rule_id: str, _user: UserContext = Depends(get_current_user)) -> PinningRule:
    return DeterminismService().get_rule(rule_id)


@router.put("/rules/{rule_id}", response_model=PinningRule)
def upsert_rule(
    rule_id: str,
    rule: PinningRule,
    _admin: UserContext = Depends(require_role(GlobalRole.ADMIN)),
) -> PinningRule:
    rule.id = rule_id
    return DeterminismService().upsert_rule(rule)


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: str, _admin: UserContext = Depends(require_role(GlobalRole.ADMIN))
) -> dict[str, bool]:
    return {"deleted": DeterminismService().delete_rule(rule_id)}


@router.get("/coverage", response_model=Coverage)
async def coverage(_user: UserContext = Depends(get_current_user)) -> Coverage:
    return await DeterminismService().coverage()


@router.post("/reconcile", response_model=list[PinnedAction])
async def reconcile(
    _admin: UserContext = Depends(require_role(GlobalRole.ADMIN)),
) -> list[PinnedAction]:
    return await DeterminismService().reconcile()

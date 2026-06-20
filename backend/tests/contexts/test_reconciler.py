"""Pinning reconciler + coverage (stories 27.2/27.3)."""

from __future__ import annotations

import pytest
from app.contexts.determinism.application.service import DeterminismService
from app.contexts.determinism.domain.models import (
    Enforcement,
    PinningRule,
    Selector,
    Trigger,
)
from app.contexts.determinism.domain.reconcile import compute_coverage, plan_actions
from app.platform import database


def _rule(rid, **over):
    base = dict(
        id=rid,
        name=rid,
        workflow="W",
        selector=Selector(ci_type="vm"),
        trigger=Trigger.ON_SCHEDULE,
        enforcement=Enforcement.ASSERT,
    )
    base.update(over)
    return PinningRule(**base)


def _cis():
    return [
        {"ci_type": "vm", "name": "web-prod-01", "tags": {"DR-Tier": "0"}},
        {"ci_type": "vm", "name": "dev-01", "tags": {}},
        {"ci_type": "datastore", "name": "ds-1", "tags": {}},
    ]


# ---- pure plan ----


def test_plan_actions_matches_per_ci_and_rule():
    rules = [
        _rule("vm_all"),
        _rule(
            "drt0",
            selector=Selector(ci_type="vm", tag_predicates={"DR-Tier": "0"}),
            enforcement=Enforcement.ENFORCE,
            trigger=Trigger.ON_CHANGE,
        ),
    ]
    plan = plan_actions(rules, _cis())
    # vm_all matches both vms (2); drt0 matches web-prod-01 only (1) → 3 actions
    assert len(plan) == 3
    assert {a.rule_id for a in plan} == {"vm_all", "drt0"}
    enforce = [a for a in plan if a.rule_id == "drt0"][0]
    assert enforce.ci == "web-prod-01" and enforce.enforcement == Enforcement.ENFORCE


def test_plan_filters_by_trigger():
    rules = [
        _rule("a", trigger=Trigger.ON_SCHEDULE),
        _rule("b", trigger=Trigger.ON_CHANGE),
    ]
    plan = plan_actions(rules, _cis(), trigger=Trigger.ON_CHANGE)
    assert {a.rule_id for a in plan} == {"b"}


def test_plan_is_deterministic():
    rules = [_rule("a"), _rule("b")]
    a = plan_actions(rules, _cis())
    b = plan_actions(rules, _cis())
    assert [x.model_dump() for x in a] == [x.model_dump() for x in b]


def test_compute_coverage_counts():
    rules = [_rule("vm_all")]
    states = iter(["compliant", "drifted"])
    cov = compute_coverage(
        rules, _cis(), workflow_exists=lambda w: False, drift_of=lambda ci, r: next(states)
    )
    rc = cov.rules[0]
    assert rc.matched == 2  # two vms
    assert rc.compliant == 1 and rc.drifted == 1
    assert rc.workflow_exists is False


# ---- service over the live CMDB ----


@pytest.fixture
def _db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.platform.app_factory  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.determinism.application.seed import seed_pinning_rules

    seed_pinning_rules()
    yield
    database.reset_for_tests()


async def test_service_reconcile_over_cmdb(_db):
    plan = await DeterminismService().reconcile()
    assert plan  # seeded rules match seeded VMs
    # the DR-Tier-0 rule should pin the db-prod-01 VM (tagged DR-Tier=0 in the sim)
    assert any(a.ci == "db-prod-01" and a.enforcement == Enforcement.ENFORCE for a in plan)


async def test_service_coverage_over_cmdb(_db):
    cov = await DeterminismService().coverage()
    assert cov.total_cis > 0
    assert cov.rules
    vm_rule = next(r for r in cov.rules if r.matched > 0)
    assert vm_rule.matched >= 1

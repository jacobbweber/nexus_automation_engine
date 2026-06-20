"""Simulated compliance evaluation: deterministic DriftReport + aggregation (story 25.2)."""

from __future__ import annotations

from app.contexts.connectors.domain.models import (
    ComplianceState,
    ConnectorKind,
    ExecutionRequest,
)
from app.contexts.connectors.infrastructure.simulation.compliance import (
    aggregate,
    evaluate_compliance,
)


def _req(action: str, target: str = "web-prod-01") -> ExecutionRequest:
    return ExecutionRequest(kind=ConnectorKind.ANSIBLE, action=action, params={"target": target})


def test_evaluation_is_deterministic():
    a = evaluate_compliance(_req("run_job_template"))
    b = evaluate_compliance(_req("run_job_template"))
    assert a.model_dump() == b.model_dump()


def test_check_only_action_is_compliant():
    r = evaluate_compliance(_req("cmdb_lookup"))
    assert r.status == ComplianceState.COMPLIANT
    assert r.drift_count == 0


def test_drift_has_desired_observed_and_reconcile():
    # find a target that drifts
    rep = None
    for t in ["web-prod-01", "db-prod-01", "app-stg-01", "x1", "x2", "x3"]:
        r = evaluate_compliance(_req("run_job_template", t))
        if r.status == ComplianceState.DRIFTED:
            rep = r
            break
    assert rep is not None, "expected at least one drifting target"
    res = rep.resources[0]
    assert res.fields and res.reconcile_action
    for fd in res.fields:
        assert fd.desired and fd.observed and fd.state == ComplianceState.DRIFTED


def test_aggregate_rolls_up_counts():
    reps = [evaluate_compliance(_req("run_job_template", t)) for t in ["a", "b", "c"]]
    agg = aggregate(reps)
    assert agg.drift_count == sum(r.drift_count for r in reps)
    assert (agg.status == ComplianceState.DRIFTED) == (agg.drift_count > 0)


def test_port_shape_satisfied():
    # the simulation evaluator matches the CompliancePort intent (async wrapper covered in 25.3)
    from app.contexts.connectors.domain.models import DriftReport

    assert isinstance(evaluate_compliance(_req("apply")), DriftReport)

"""CMDB health checker — pure check_ci across healthy / degraded / unhealthy CIs (story 24.3)."""

from __future__ import annotations

import pytest
from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
from app.contexts.cmdb.application.service import CmdbHealthService
from app.contexts.cmdb.domain.health import HealthStatus, check_ci
from app.contexts.cmdb.domain.lineage import (
    Cardinality,
    Direction,
    LineageRelationship,
    LineageSpec,
)
from app.contexts.cmdb.domain.models import CITypeSchema, FieldDef, FieldType
from app.platform import database


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.cmdb.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def _vm_schema() -> CITypeSchema:
    return CITypeSchema(
        type="vm",
        label="VM",
        naming_pattern=r"^[a-z][a-z0-9-]+$",
        required_tags=["owner"],
        fields=[
            FieldDef(name="name", label="Name", required=True),
            FieldDef(name="cpu", label="vCPU", datatype=FieldType.INTEGER, required=True),
            FieldDef(
                name="env",
                label="Env",
                datatype=FieldType.ENUM,
                allowed_values=["Production", "Development"],
                required=True,
            ),
        ],
    )


def _vm_lineage() -> LineageSpec:
    return LineageSpec(
        type="vm",
        relationships=[
            LineageRelationship(
                name="host",
                target_type="host",
                direction=Direction.UP,
                cardinality=Cardinality.ONE,
                required=True,
            ),
        ],
    )


def _healthy_ci() -> dict:
    return {
        "id": "ci-1",
        "name": "web-prod-01",
        "ci_type": "vm",
        "cpu": 4,
        "env": "Production",
        "tags": {"owner": "a.khan"},
        "relationships": {"host": ["host-1"]},
    }


def test_healthy_ci_scores_100():
    r = check_ci(_healthy_ci(), _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    assert r.status == HealthStatus.HEALTHY
    assert r.score == 100
    assert r.all_issues == []


def test_missing_required_field_flagged():
    ci = _healthy_ci()
    del ci["cpu"]
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    assert any(i.code == "missing_required" and i.target == "cpu" for i in r.field_issues)
    assert r.score < 100
    assert any("vCPU" in h for h in r.remediation_hints)


def test_invalid_enum_and_integer_flagged():
    ci = _healthy_ci()
    ci["env"] = "Mars"
    ci["cpu"] = "lots"
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    codes = {i.code for i in r.field_issues}
    assert "invalid_value" in codes


def test_naming_violation_flagged():
    ci = _healthy_ci()
    ci["name"] = "WEB_PROD_01"  # uppercase/underscore violates pattern
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    assert any(i.code == "naming_violation" for i in r.field_issues)


def test_missing_tag_is_a_warning():
    ci = _healthy_ci()
    ci["tags"] = {}
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    assert any(i.code == "missing_tag" and i.severity == "warning" for i in r.tag_issues)


def test_missing_required_relationship_flagged():
    ci = _healthy_ci()
    ci["relationships"] = {}
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids=set())
    assert any(i.code == "missing_relationship" and i.target == "host" for i in r.lineage_issues)


def test_orphaned_reference_flagged():
    ci = _healthy_ci()
    ci["relationships"] = {"host": ["ghost-host"]}
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    assert any(i.code == "orphaned_reference" for i in r.lineage_issues)


def test_cardinality_violation_flagged():
    ci = _healthy_ci()
    ci["relationships"] = {"host": ["host-1", "host-2"]}
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1", "host-2"})
    assert any(i.code == "cardinality_violation" for i in r.lineage_issues)


def test_unhealthy_when_many_errors():
    ci = {"id": "ci-x", "name": "BAD", "ci_type": "vm", "tags": {}, "relationships": {}}
    r = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids=set())
    assert r.status == HealthStatus.UNHEALTHY
    assert r.score < 60


def test_scoring_is_deterministic():
    ci = _healthy_ci()
    del ci["cpu"]
    a = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    b = check_ci(ci, _vm_schema(), _vm_lineage(), known_ci_ids={"host-1"})
    assert a.score == b.score and a.model_dump() == b.model_dump()


def test_service_resolves_schema_and_lineage_from_seed():
    seed_cmdb_schemas()
    seed_cmdb_lineage()
    svc = CmdbHealthService()
    # a vm missing its required relationships + tags + fields → degraded/unhealthy with hints
    ci = {"id": "ci-9", "name": "app-stg-01", "ci_type": "vm", "tags": {}, "relationships": {}}
    report = svc.check(ci)
    assert report.ci_type == "vm"
    assert report.status in (HealthStatus.DEGRADED, HealthStatus.UNHEALTHY)
    assert report.remediation_hints

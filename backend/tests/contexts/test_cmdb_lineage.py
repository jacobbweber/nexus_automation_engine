"""CMDB lineage: pure validators (incl. cycle detection) + repo/service + seed (story 24.2)."""

from __future__ import annotations

import pytest
from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
from app.contexts.cmdb.application.service import CmdbLineageService
from app.contexts.cmdb.domain.lineage import (
    Cardinality,
    Direction,
    LineageRelationship,
    LineageSpec,
    validate_lineage,
    validate_lineage_set,
)
from app.platform import database
from app.shared_kernel.errors import NotFoundError, ValidationError


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


def _rel(name, target, direction=Direction.UP, required=True):
    return LineageRelationship(
        name=name,
        target_type=target,
        direction=direction,
        cardinality=Cardinality.ONE,
        required=required,
    )


# ---- pure validators -----------------------------------------------------------------------------


def test_valid_lineage_has_no_errors():
    spec = LineageSpec(type="vm", relationships=[_rel("host", "host")])
    assert validate_lineage(spec, {"vm", "host"}) == []


def test_unknown_target_type_rejected():
    spec = LineageSpec(type="vm", relationships=[_rel("host", "nope")])
    assert any("unknown CI type" in e for e in validate_lineage(spec, {"vm"}))


def test_duplicate_relationship_name_rejected():
    spec = LineageSpec(type="vm", relationships=[_rel("host", "host"), _rel("host", "host")])
    assert any("duplicate relationship" in e for e in validate_lineage(spec, {"vm", "host"}))


def test_required_up_cycle_detected():
    specs = [
        LineageSpec(type="a", relationships=[_rel("b", "b")]),
        LineageSpec(type="b", relationships=[_rel("a", "a")]),
    ]
    errs = validate_lineage_set(specs)
    assert any("cycle" in e for e in errs)


def test_down_relationship_does_not_count_as_cycle():
    # application -> vm is DOWN; vm -> host is UP. No required-up cycle.
    specs = [
        LineageSpec(type="application", relationships=[_rel("members", "vm", Direction.DOWN)]),
        LineageSpec(type="vm", relationships=[_rel("host", "host")]),
        LineageSpec(type="host", relationships=[]),
    ]
    assert validate_lineage_set(specs) == []


# ---- repo / service ------------------------------------------------------------------------------


def test_upsert_requires_known_target_type():
    seed_cmdb_schemas()  # so "host" is a known type
    svc = CmdbLineageService()
    svc.upsert_lineage(LineageSpec(type="vm", relationships=[_rel("host", "host")]))
    assert svc.get_lineage("vm").relationships[0].target_type == "host"


def test_upsert_rejects_unknown_target():
    seed_cmdb_schemas()
    svc = CmdbLineageService()
    with pytest.raises(ValidationError):
        svc.upsert_lineage(LineageSpec(type="vm", relationships=[_rel("x", "ghost")]))


def test_get_unknown_lineage_raises():
    with pytest.raises(NotFoundError):
        CmdbLineageService().get_lineage("nope")


# ---- seed --------------------------------------------------------------------------------------


def test_seed_lineage_is_valid_and_idempotent():
    seed_cmdb_schemas()
    created = seed_cmdb_lineage()
    assert created >= 6
    specs = CmdbLineageService().list_lineage()
    # the seeded set is internally consistent (known targets, no required-up cycle)
    assert validate_lineage_set(specs) == []
    types = {s.type for s in specs}
    assert {"vm", "host", "cluster", "datastore", "volume", "backup_policy", "application"} <= types
    assert seed_cmdb_lineage() == 0

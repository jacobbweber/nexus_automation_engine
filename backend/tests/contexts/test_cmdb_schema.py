"""CMDB CI type schema: pure validator + registry repository/service + seed (story 24.1)."""

from __future__ import annotations

import pytest
from app.contexts.cmdb.application.seed import seed_cmdb_schemas
from app.contexts.cmdb.application.service import CmdbSchemaService
from app.contexts.cmdb.domain.models import (
    CITypeSchema,
    FieldDef,
    FieldType,
    validate_schema,
)
from app.contexts.cmdb.infrastructure.repository import CITypeSchemaRepository
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


# ---- pure validator (no I/O) ------------------------------------------------------------------


def _valid() -> CITypeSchema:
    return CITypeSchema(
        type="vm",
        label="Virtual Machine",
        fields=[
            FieldDef(name="name", label="Name", required=True),
            FieldDef(
                name="env",
                label="Env",
                datatype=FieldType.ENUM,
                allowed_values=["Production", "Development"],
                required=True,
            ),
        ],
        naming_pattern=r"^[a-z0-9-]+$",
    )


def test_valid_schema_has_no_errors():
    assert validate_schema(_valid()) == []


def test_enum_field_requires_allowed_values():
    s = _valid()
    s.fields.append(FieldDef(name="tier", label="Tier", datatype=FieldType.ENUM))
    errs = validate_schema(s)
    assert any("allowed_values" in e for e in errs)


def test_duplicate_field_names_rejected():
    s = _valid()
    s.fields.append(FieldDef(name="name", label="Dup"))
    assert any("duplicate field name" in e for e in validate_schema(s))


def test_invalid_regex_rejected():
    s = _valid()
    s.fields.append(FieldDef(name="x", label="X", regex="([unclosed"))
    assert any("invalid regex" in e for e in validate_schema(s))


def test_bad_naming_pattern_rejected():
    s = _valid()
    s.naming_pattern = "([nope"
    assert any("naming_pattern" in e for e in validate_schema(s))


def test_allowed_values_on_non_enum_rejected():
    s = _valid()
    s.fields.append(FieldDef(name="z", label="Z", allowed_values=["a"]))
    assert any("not an enum" in e for e in validate_schema(s))


def test_default_must_be_in_allowed_values():
    s = _valid()
    s.fields.append(
        FieldDef(
            name="region",
            label="Region",
            datatype=FieldType.ENUM,
            allowed_values=["us", "eu"],
            default="apac",
        )
    )
    assert any("not in allowed_values" in e for e in validate_schema(s))


# ---- registry repository / service -------------------------------------------------------------


def test_upsert_and_get_roundtrip():
    svc = CmdbSchemaService()
    svc.upsert_schema(_valid())
    got = svc.get_schema("vm")
    assert got.type == "vm"
    assert {f.name for f in got.fields} == {"name", "env"}


def test_upsert_rejects_invalid_schema():
    svc = CmdbSchemaService()
    bad = _valid()
    bad.fields.append(FieldDef(name="tier", label="Tier", datatype=FieldType.ENUM))
    with pytest.raises(ValidationError):
        svc.upsert_schema(bad)


def test_get_unknown_type_raises():
    with pytest.raises(NotFoundError):
        CmdbSchemaService().get_schema("nope")


def test_upsert_is_idempotent_on_type():
    repo = CITypeSchemaRepository()
    svc = CmdbSchemaService(repo)
    svc.upsert_schema(_valid())
    svc.upsert_schema(_valid())
    assert repo.count() == 1


# ---- seed --------------------------------------------------------------------------------------


def test_seed_populates_core_types_and_is_idempotent():
    created = seed_cmdb_schemas()
    assert created >= 6
    types = {s.type for s in CmdbSchemaService().list_schemas()}
    assert {"vm", "datastore", "cluster", "volume", "backup_policy", "application", "host"} <= types
    # every seeded schema is itself valid
    for s in CmdbSchemaService().list_schemas():
        assert validate_schema(s) == []
    assert seed_cmdb_schemas() == 0

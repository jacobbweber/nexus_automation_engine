"""Pinning rules: pure matcher + repo + seed (story 27.1)."""

from __future__ import annotations

import pytest
from app.contexts.determinism.application.seed import seed_pinning_rules
from app.contexts.determinism.domain.models import (
    Enforcement,
    PinningRule,
    Selector,
    Trigger,
    match_rules,
    matches,
)
from app.contexts.determinism.infrastructure.repository import PinningRuleRepository
from app.platform import database


def _rule(**over):
    base = dict(
        id="r1",
        name="r1",
        workflow="W",
        selector=Selector(ci_type="vm"),
        trigger=Trigger.ON_SCHEDULE,
        enforcement=Enforcement.ASSERT,
    )
    base.update(over)
    return PinningRule(**base)


def _vm(**tags):
    return {"ci_type": "vm", "name": "x", "tags": dict(tags), "env": "Production"}


# ---- matcher (pure) ----


def test_type_selector_matches():
    assert matches(_rule(), _vm())
    assert not matches(_rule(), {"ci_type": "datastore", "tags": {}})


def test_tag_predicate():
    r = _rule(selector=Selector(ci_type="vm", tag_predicates={"DR-Tier": "0"}))
    assert matches(r, _vm(**{"DR-Tier": "0"}))
    assert not matches(r, _vm(**{"DR-Tier": "1"}))
    assert not matches(r, _vm())


def test_field_predicate():
    r = _rule(selector=Selector(field_predicates={"env": "Production"}))
    assert matches(r, _vm())
    assert not matches(r, {"ci_type": "vm", "env": "Development", "tags": {}})


def test_match_rules_orders_by_priority_and_skips_disabled():
    rules = [
        _rule(id="a", name="a", priority=50),
        _rule(id="b", name="b", priority=10),
        _rule(id="c", name="c", priority=5, enabled=False),
    ]
    hits = match_rules(rules, _vm())
    assert [r.id for r in hits] == ["b", "a"]  # disabled c skipped; sorted by priority


# ---- repo + seed ----


@pytest.fixture
def _db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.determinism.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    yield
    database.reset_for_tests()


def test_repo_roundtrip_and_delete(_db):
    repo = PinningRuleRepository()
    repo.upsert(_rule())
    assert repo.get("r1").workflow == "W"
    assert repo.count() == 1
    assert repo.delete("r1") is True
    assert repo.count() == 0


def test_seed_is_idempotent_and_demonstrates(_db):
    created = seed_pinning_rules()
    assert created == 2
    rules = PinningRuleRepository().list_all()
    # the DR-Tier-0 rule matches the seeded db-prod-01 VM (tags include DR-Tier=0)
    drt = next(r for r in rules if "DR-Tier" in r.selector.tag_predicates)
    assert drt.enforcement == Enforcement.ENFORCE
    assert matches(drt, {"ci_type": "vm", "tags": {"DR-Tier": "0"}})
    assert seed_pinning_rules() == 0

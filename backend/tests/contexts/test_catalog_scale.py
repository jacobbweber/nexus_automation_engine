"""Tests for the large seeded catalog + faceted filtering."""

from __future__ import annotations

import pytest
from app.contexts.automation_catalog.application.seed import seed_templates
from app.contexts.automation_catalog.application.service import CatalogService
from app.contexts.automation_catalog.domain.models import ApprovalState
from app.contexts.automation_catalog.infrastructure.repository import TemplateRepository
from app.platform import database


@pytest.fixture(autouse=True)
def _clean_db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.automation_catalog.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    yield
    database.reset_for_tests()


def test_seed_creates_large_multivendor_catalog():
    created = seed_templates(TemplateRepository())
    assert created >= 20
    svc = CatalogService()
    vendors = {t.vendor for t in svc.list_all(approval_state=ApprovalState.APPROVED)}
    assert {"VMware", "Pure Storage", "Cohesity", "ServiceNow"} <= vendors


def test_facets_counts_by_domain_and_vendor():
    seed_templates(TemplateRepository())
    facets = CatalogService().facets()
    assert facets["domain"].get("Storage", 0) > 0
    assert facets["vendor"].get("VMware", 0) > 0


def test_filter_by_domain_and_vendor():
    seed_templates(TemplateRepository())
    svc = CatalogService()
    storage = svc.list_all(approval_state=ApprovalState.APPROVED, domain="Storage")
    assert storage and all(t.domain == "Storage" for t in storage)
    pure = svc.list_all(approval_state=ApprovalState.APPROVED, vendor="Pure Storage")
    assert pure and all(t.vendor == "Pure Storage" for t in pure)


def test_search_matches_name_and_tags():
    seed_templates(TemplateRepository())
    svc = CatalogService()
    assert any("datastore" in t.name.lower() for t in svc.list_all(search="datastore"))
    assert svc.list_all(search="cohesity")  # tag match


def test_controlled_items_are_high_risk():
    seed_templates(TemplateRepository())
    svc = CatalogService()
    eradicate = next(t for t in svc.list_all(search="eradicate"))
    assert eradicate.risk.value in ("high", "critical")

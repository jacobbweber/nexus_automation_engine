"""Canonical config serializer — a deterministic on-disk snapshot of all config artifacts.

Stable file paths + stable key-ordered JSON with volatile audit timestamps stripped, so that
re-serializing unchanged config is byte-identical (and Git diffs are meaningful). This is what the
GitOps backbone commits. Pure read: it reads the config repos and returns {path: content}.
"""

from __future__ import annotations

import json
from typing import Any

# Volatile audit fields (change on every save) — stripped so unchanged config stays byte-identical.
_VOLATILE = {"updated_at", "created_at", "decided_at", "decided_by"}


def _strip(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in _VOLATILE}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def _canonical(model: Any) -> str:
    """Stable JSON for a pydantic model (or dict): sorted keys, volatile fields removed."""
    data = model.model_dump(mode="json") if hasattr(model, "model_dump") else model
    return json.dumps(_strip(data), sort_keys=True, indent=2, ensure_ascii=False, default=str)


def snapshot() -> dict[str, str]:
    """Return {relative_path: canonical_json} for every config artifact. Deterministic."""
    out: dict[str, str] = {}

    from app.contexts.automation_catalog.application.service import CatalogService
    from app.contexts.change_management.application.service import ChangeService
    from app.contexts.cmdb.application.service import CmdbLineageService, CmdbSchemaService
    from app.contexts.determinism.infrastructure.repository import PinningRuleRepository
    from app.contexts.lifecycle_validation.application.service import ValidationService
    from app.contexts.orchestration_canvas.application.service import CanvasService
    from app.contexts.scheduling.application.service import ScheduleService

    for wf in CanvasService().list_workflows():
        out[f"workflows/{wf.id}.json"] = _canonical(wf)
    for s in CmdbSchemaService().list_schemas():
        out[f"cmdb/schemas/{s.type}.json"] = _canonical(s)
    for lin in CmdbLineageService().list_lineage():
        out[f"cmdb/lineage/{lin.type}.json"] = _canonical(lin)
    for rule in PinningRuleRepository().list_all():
        out[f"pinning/{rule.id}.json"] = _canonical(rule)
    for tpl in CatalogService().list_all():
        out[f"catalog/{tpl.id}.json"] = _canonical(tpl)
    out["policy/validation.json"] = _canonical(ValidationService().get_policy())
    for sched in ScheduleService().list_all():
        out[f"schedules/{sched.id}.json"] = _canonical(sched)
    for ct in ChangeService().list_templates():
        out[f"change-templates/{ct.id}.json"] = _canonical(ct)

    return out

"""The deterministic CI health checker — the payoff of the cmdb context.

Given a CI record, its CITypeSchema, and its LineageSpec, produce a CIHealthReport: field issues,
lineage issues, tag issues, a stable health score, a status, and remediation hints. Pure (no I/O),
deterministic (no AI, ADR-0008). The lifecycle gate, pickers, pinning, and review-impact consume it.

CI record shape (a plain dict, as the ServiceNow ACL connector yields it, enriched):
    {
      "id": "ci-1001", "name": "web-prod-01", "ci_type": "vm",
      <field>: <value>, ...,
      "tags": {"owner": "a.khan", ...},
      "relationships": {"host": ["host-1"], "datastores": ["ds-1", "ds-2"], ...},
    }
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field

from app.contexts.cmdb.domain.lineage import Cardinality, LineageSpec
from app.contexts.cmdb.domain.models import CITypeSchema, FieldType

# Deterministic score weights (documented so the score is explainable and stable).
_W_REQUIRED_FIELD = 12
_W_INVALID_VALUE = 10
_W_NAMING = 10
_W_REQUIRED_REL = 15
_W_CARDINALITY = 8
_W_ORPHAN = 8
_W_MISSING_TAG = 6


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class Issue(BaseModel):
    code: str
    target: str  # the field name, relationship name, or tag key
    message: str
    severity: Severity = Severity.ERROR
    weight: int = 0


class CIHealthReport(BaseModel):
    ci_id: str
    ci_type: str
    status: HealthStatus
    score: int
    field_issues: list[Issue] = Field(default_factory=list)
    lineage_issues: list[Issue] = Field(default_factory=list)
    tag_issues: list[Issue] = Field(default_factory=list)
    remediation_hints: list[str] = Field(default_factory=list)

    @property
    def all_issues(self) -> list[Issue]:
        return [*self.field_issues, *self.lineage_issues, *self.tag_issues]


def _is_empty(v: object) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def _valid_value(value: object, datatype: FieldType, allowed: list[str] | None) -> bool:
    if datatype == FieldType.ENUM:
        return allowed is not None and str(value) in allowed
    if datatype == FieldType.INTEGER:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        return isinstance(value, str) and value.strip().lstrip("-").isdigit()
    if datatype == FieldType.BOOLEAN:
        return isinstance(value, bool) or str(value).lower() in {"true", "false"}
    return True  # string / datetime / reference — presence is enough here


def check_ci(
    ci: dict[str, object],
    schema: CITypeSchema,
    lineage: LineageSpec | None = None,
    known_ci_ids: set[str] | None = None,
) -> CIHealthReport:
    """Evaluate a CI against its schema (+ optional lineage). Returns a deterministic report."""
    field_issues: list[Issue] = []
    lineage_issues: list[Issue] = []
    tag_issues: list[Issue] = []
    hints: list[str] = []

    ci_id = str(ci.get("id") or ci.get("name") or "?")

    # ---- fields ----
    for f in schema.fields:
        present = f.name in ci and not _is_empty(ci.get(f.name))
        if f.required and not present:
            field_issues.append(
                Issue(
                    code="missing_required",
                    target=f.name,
                    weight=_W_REQUIRED_FIELD,
                    message=f"required field '{f.label}' is missing",
                )
            )
            hints.append(f"Populate required field '{f.label}'.")
            continue
        if present:
            val = ci.get(f.name)
            if not _valid_value(val, f.datatype, f.allowed_values):
                field_issues.append(
                    Issue(
                        code="invalid_value",
                        target=f.name,
                        weight=_W_INVALID_VALUE,
                        message=f"field '{f.label}' value '{val}' is not a valid {f.datatype}",
                    )
                )
                hints.append(f"Correct '{f.label}' to a valid {f.datatype} value.")
            elif f.regex and isinstance(val, str) and not re.fullmatch(f.regex, val):
                field_issues.append(
                    Issue(
                        code="invalid_format",
                        target=f.name,
                        weight=_W_INVALID_VALUE,
                        message=f"field '{f.label}' value does not match the required format",
                    )
                )

    # naming pattern on the CI name
    name = ci.get("name")
    if (
        schema.naming_pattern
        and isinstance(name, str)
        and not re.fullmatch(schema.naming_pattern, name)
    ):
        field_issues.append(
            Issue(
                code="naming_violation",
                target="name",
                weight=_W_NAMING,
                message=f"name '{name}' violates the naming convention",
            )
        )
        hints.append("Rename the CI to match the naming convention.")

    # ---- tags ----
    _tags = ci.get("tags")
    tags: dict[str, object] = _tags if isinstance(_tags, dict) else {}
    for tag in schema.required_tags:
        if _is_empty(tags.get(tag)):
            tag_issues.append(
                Issue(
                    code="missing_tag",
                    target=tag,
                    weight=_W_MISSING_TAG,
                    severity=Severity.WARNING,
                    message=f"required tag '{tag}' is missing",
                )
            )
            hints.append(f"Add required tag '{tag}'.")

    # ---- lineage ----
    _rels = ci.get("relationships")
    rels: dict[str, object] = _rels if isinstance(_rels, dict) else {}
    if lineage:
        for r in lineage.relationships:
            targets = rels.get(r.name) or []
            if not isinstance(targets, list):
                targets = [targets]
            if r.required and not targets:
                lineage_issues.append(
                    Issue(
                        code="missing_relationship",
                        target=r.name,
                        weight=_W_REQUIRED_REL,
                        message=f"required relationship '{r.name}' (-> {r.target_type}) is missing",
                    )
                )
                hints.append(f"Link a '{r.target_type}' as '{r.name}'.")
                continue
            if r.cardinality == Cardinality.ONE and len(targets) > 1:
                lineage_issues.append(
                    Issue(
                        code="cardinality_violation",
                        target=r.name,
                        weight=_W_CARDINALITY,
                        message=(
                            f"'{r.name}' expects one {r.target_type} but {len(targets)} are set"
                        ),
                    )
                )
            if known_ci_ids is not None:
                for t in targets:
                    if str(t) not in known_ci_ids:
                        lineage_issues.append(
                            Issue(
                                code="orphaned_reference",
                                target=r.name,
                                weight=_W_ORPHAN,
                                message=f"'{r.name}' references unknown CI '{t}'",
                            )
                        )
                        hints.append(f"Fix or remove the dangling '{r.name}' reference to '{t}'.")

    # ---- score + status ----
    all_issues = [*field_issues, *lineage_issues, *tag_issues]
    score = max(0, 100 - sum(i.weight for i in all_issues))
    has_error = any(i.severity == Severity.ERROR for i in all_issues)
    if score >= 90 and not has_error:
        status = HealthStatus.HEALTHY
    elif score >= 60:
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.UNHEALTHY

    # de-duplicate hints preserving order
    seen: set[str] = set()
    ordered_hints: list[str] = []
    for h in hints:
        if h not in seen:
            seen.add(h)
            ordered_hints.append(h)

    return CIHealthReport(
        ci_id=ci_id,
        ci_type=schema.type,
        status=status,
        score=score,
        field_issues=field_issues,
        lineage_issues=lineage_issues,
        tag_issues=tag_issues,
        remediation_hints=ordered_hints,
    )

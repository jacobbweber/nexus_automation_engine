# ADR-0006 — Origin-story lifecycle validation as a single shared gate

**Status:** Accepted (2026-06-19)

## Context
Operator requirement: no automation should run unless it is *provably valid* — carrying required
metadata (authored_by, approved_date, last_updated, last_reviewed, CI type + heritage) and
**validated against the CMDB** at build/save and again pre-launch. A run must be rejected when its
target contradicts the CMDB CI lifecycle (e.g. a destructive action on a datastore that is a
cluster member, a retired CI, or a CI-type mismatch). Crucially, the *check itself* should be one
admin-editable thing that every automation relies on — not logic scattered per feature.

## Decision
Introduce a `lifecycle_validation` bounded context owning a **single, admin-editable
`ValidationPolicy`** (required fields, max review age, CMDB-consistency toggles) and a
`ValidationService` that all execution paths consult. Validation has two stages —
`validate_for_build` (metadata completeness/freshness) and `validate_for_execution`
(metadata + CMDB consistency, resolving the target CI via the ServiceNow CMDB **connector port**,
so it stays vendor-neutral). The catalog execute path calls `enforce_for_execution`, which raises
`ValidationRejected` (422) on any violation. Enforcement is gated by
`NEXUS_ENFORCE_LIFECYCLE_VALIDATION` (on by default; off in the test suite). A
`/governance/validation/review-status` endpoint powers the **pruning & review** dashboard
(fresh/stale/never-reviewed + oldest).

The "single shared workflow admins edit" is realized as the editable **policy** (the rules), with
the validation service as its executor — equivalent power without making every run recursively
execute a canvas workflow (which would be heavy and circular). A future enhancement can expose the
policy as a canvas-authored workflow.

## Consequences
**Good:** one governing object gates all execution; metadata becomes mandatory and auditable; CMDB
contradictions are caught before runtime; the pruning dashboard surfaces stale automation; the
gate doubles as the "central execution gate" the security audit (S2) called for.
**Bad / costs:** currently wired into the catalog execute path; direct `/jobs/execute` and canvas
`automation_task` execution still need the same gate (tracked follow-up) for full coverage;
target-CI resolution is name-based against the (sim) CMDB; the "policy as an editable canvas
workflow" is approximated by structured policy fields for now.

## Alternatives considered
- **Per-feature validation logic:** rejected — scatters rules, drifts, no single source of truth.
- **Every run executes a validation *canvas workflow* first:** elegant but heavy/circular for the
  hot path; the editable policy + service achieves the same governance more simply (revisitable).

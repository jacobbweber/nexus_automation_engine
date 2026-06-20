# ADR-0009 — CMDB Schema & Lineage as a bounded context

**Status:** Accepted (2026-06-20)

## Context

The v4.0 Deterministic Governance line ([vision](../00_foundation/vision_deterministic_governance.md))
needs an objective, machine-checkable definition of what a "healthy / correct" configuration item
(CI) is — per CI type — so that:

- the lifecycle-validation gate ([ADR-0006](./ADR-0006-lifecycle-validation-gate.md)) can reject runs
  against incomplete/unhealthy CIs with real signal;
- deterministic pinning (M27) can select CIs by typed fields/tags and assert guaranteed workflows;
- review packets (M26) can compute meaningful blast radius and impact.

Today CI shape is implicit: the simulated ServiceNow CMDB returns ad-hoc dicts, and
`lifecycle_validation` hard-codes a few field checks. There is no place to *define* what a `vm`,
`datastore`, or `cluster` must contain, nor what relationships make a CI "whole" (its **lineage**).

We considered three placements:
1. Extend `lifecycle_validation` with schema knowledge.
2. Put schemas inside `connectors` (next to the ServiceNow adapter).
3. A new bounded context that owns CI type schemas, lineage specs, and the health checker.

## Decision

Introduce a new bounded context **`cmdb`** (specs under `specs/07_cmdb/`). It owns:

- **CI Type Schema** — schema-as-data: per CI type, the field definitions (name, datatype, required,
  allowed values / regex, default, sensitivity), required tags, and naming pattern. Versioned,
  admin-maintainable, validated by a **deterministic** validator (no AI, per
  [ADR-0008](./ADR-0008-no-in-product-ai.md)) — the same proven pattern as `nexus-theme/v1` and the
  canvas `node_specs`.
- **Lineage Spec** — per CI type, the typed required relationships (target type, direction,
  cardinality, required) that make a CI whole.
- **CI Health Checker** — a pure function that evaluates a CI (its record + resolved relationships)
  against its schema + lineage and returns a deterministic **CI Health Report** (field/lineage/tag
  issues, a score, remediation hints, status).

The **`connectors` ServiceNow adapter stays the Anti-Corruption Layer** that fetches raw CI data;
`cmdb` interprets that data against schemas. **`lifecycle_validation` becomes a consumer** of the
health checker (it does not absorb schema ownership). Contexts integrate only through published
application contracts (`architecture.md` §4).

The slice follows the standard layout (`domain` pure → `application` use cases → `infrastructure`
adapters → `api`), persisted with synchronous SQLAlchemy ([ADR-0004](./ADR-0004-synchronous-sqlalchemy.md))
storing each schema/lineage as a JSON document row keyed by CI type.

## Consequences

**Good**
- A single, authoritative, versioned definition of CI correctness that multiple contexts consume.
- "Healthy CI" becomes objective and machine-checkable — the precondition for pinning, review impact,
  and compliance.
- New integrations declare their CI shapes once; the checker, gate, pickers, and pinning all benefit.
- Pure checker = trivially unit-testable and deterministic.

**Bad / costs**
- A new context to maintain, and a migration path: `lifecycle_validation`'s ad-hoc CMDB checks must
  be re-pointed at the checker without regressing existing behavior.
- The simulated CMDB must grow richer (relationships, tags) to give the checker real signal — done
  additively to avoid breaking existing connector/validation tests.

## Alternatives considered
- **Extend `lifecycle_validation`** — rejected: conflates "the gate" (a policy decision point) with
  "the model of CI correctness"; the latter is consumed by several contexts, not just the gate.
- **Schemas inside `connectors`** — rejected: would leak a vendor-shaped concern (ServiceNow tables)
  into what is a Nexus-domain contract; violates the ACL boundary (vendor models translate *in*, the
  CI-correctness contract is ours).

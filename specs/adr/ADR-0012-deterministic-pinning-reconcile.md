# ADR-0012 — Deterministic policy pinning & reconcile loop

**Status:** Accepted (2026-06-20)

## Context

The operator's requirement ([vision](../00_foundation/vision_deterministic_governance.md) §5):
*deterministic management* — a place to declare rules that **guarantee** a workflow for a CI or class
of CIs (e.g. every VM is continuously tag/CMDB-validated; any VM tagged `DR-Tier=0` is guaranteed a
Zerto DR VPG). The value isn't a trigger list — it's **management-by-invariant**: "what is guaranteed
about my estate, and where does reality not match?"

## Decision

A new bounded context **`determinism`**:

- **PinningRule** = `selector (CI type + tag/field predicates, over the M24 schema) → guaranteed
  workflow + trigger (create | change | schedule | on-demand) + enforcement (assert | enforce | gate)
  + priority`. A pure matcher selects the CIs a rule governs.
- **Reconciler** — `plan_actions(rules, cis, trigger?)` produces a deterministic *pinned-actions plan*
  (per CI × matching rule). `assert` runs in compliance mode (M25, no mutation); `enforce` opens a
  review-gated reconcile run (M26); `gate` blocks the triggering change until the pinned check passes.
  On-change is wired to the CI-change path (M26.5); on-schedule rides the M11 cadence; drift becomes
  incidents (M16) via the compliance sweep.
- **Coverage** — `compute_coverage(...)` answers the headline question per rule: matched CIs, whether
  the guaranteed workflow exists, and (for assert rules) compliant vs drifted.
- A **Guardrails** admin page authors rules with a schema-driven selector builder and shows coverage.

This composes the prior pillars rather than duplicating them: selectors over M24 schemas, assert via
M25 compliance, enforce via M26 review, cadence/incidents via M11/M16. Everything deterministic
([ADR-0008](./ADR-0008-no-in-product-ai.md)).

## Consequences

**Good**
- Desired state is *declared and guaranteed*, not hoped — and the gap is always visible (coverage).
- One rule set ties together the whole 4.0 line (contract → compliance → review → cadence/incidents).
- The reconciler is pure + deterministic → trivially testable; the plan drives both API and UI.

**Bad / costs**
- Rules reference workflows by name/id; a missing workflow is surfaced (coverage `workflow_exists`)
  but not auto-created — authoring the guaranteed workflows is a human step.
- Full closed-loop *enforcement execution* (auto-running enforce reconciles after approval) is
  represented in the plan + opens approvals, but the post-approval auto-run is left to the normal
  run path; deeper automation is a follow-up.

## Alternatives considered
- **Event-driven rules engine per connector** — rejected: couples guarantees to vendors; selectors
  over the Nexus CMDB schema (M24) keep it vendor-agnostic.
- **Ad-hoc scheduled jobs** (just schedule the validators) — rejected: that's the "hope someone
  scheduled it" failure mode; pinning makes the guarantee + its coverage first-class.

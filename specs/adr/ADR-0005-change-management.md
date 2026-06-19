# ADR-0005 — Change management as a 2.0 bounded context

**Status:** Accepted (2026-06-18)

## Context
The 2.0 ops-engineering review (`specs/00_foundation/vision_2_0.md`) identified change control as
the flagship gap: turning ad-hoc automation into audited, CAB-aware change is the biggest enabler
for letting operators self-serve against production. The operator explicitly seeded this idea
(per-job "automatic change control" toggle, standard change-template ID + fields, configurable).

## Decision
Introduce a new bounded context **`change_management`** (vertical slice) owning: reusable
**change templates** (standard ITSM fields: assignment group, category, risk, impact, CAB-required),
per-resource **change-control policies** (`auto_change_control`, `change_template_id`,
`require_approved_change`), and **change records** (CHG numbers, lifecycle states). The
`automation_catalog` execute path calls `ChangeService.evaluate_for_execution(...)` before
dispatch: if a policy applies it opens a change and stamps the number onto the job; if the policy
requires an approved change and the opened change is not approved (e.g. CAB-required), the live
run is blocked (`ConflictError`). Standard (non-CAB) changes auto-approve; CAB-required changes
await assessment. The execution `Job` gains an optional `change_number` for audit linkage.

Change record *creation* is modeled in this context (simulation-grade approval rules) rather than
forced through the ServiceNow connector now; a real ServiceNow change adapter can implement the
same `ChangeService` boundary later without changing callers.

## Consequences
**Good:** governed, audited change wraps execution with one policy toggle; operators self-serve
safely; the boundary is clean (catalog/execution depend only on `ChangeService`); extends to real
ITSM later via an adapter.
**Bad / costs:** change *close-out* on job completion is not yet wired (records open but aren't
auto-closed) — a refinement; canvas runs don't yet consult policy (only catalog execute does);
approval of CAB changes is simulated, not a real workflow.

## Alternatives considered
- **Bolt fields onto the catalog/execution contexts:** rejected — change management is its own
  domain with its own lifecycle; mixing it in would blur boundaries.
- **Route change creation through the ServiceNow connector now:** deferred — the policy/record
  model is needed regardless; the connector becomes one implementation of the boundary later.

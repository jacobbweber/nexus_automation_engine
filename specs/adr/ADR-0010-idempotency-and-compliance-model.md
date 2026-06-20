# ADR-0010 — Idempotency contract & drift/compliance model

**Status:** Accepted (2026-06-20)

## Context

The v4.0 mandate ([vision](../00_foundation/vision_deterministic_governance.md) §3) is that **all
automation is idempotent and continuously re-runnable for compliance** — anyone can run anything,
anytime, to preview impact and drift without mutating. Today "idempotent" is an aspiration with no
representation in the model, and there is no first-class notion of *drift* (desired vs observed).

We need: (1) a way to *declare and enforce* re-run safety per building block, and (2) a model +
connector capability to *evaluate* compliance and report drift deterministically (no AI, per
[ADR-0008](./ADR-0008-no-in-product-ai.md)).

## Decision

1. **Idempotency class** — a small shared-kernel enum `IdempotencyClass`
   (`idempotent | check_only | non_idempotent`) carried by every `ConnectorAction` and catalog
   `Template`. A deterministic `infer_idempotency(action)` classifies by name (destructive verbs →
   non-idempotent; read/plan verbs → check-only; else idempotent). `ConnectorAction` auto-classifies
   from its name when left at the default, so all adapters self-describe without per-adapter edits;
   adapters/templates may override explicitly. `is_flagged` marks non-idempotent (mutating) blocks
   — the ones that cannot be blindly re-run for compliance.

2. **Drift / compliance model** (M25.2+) — a `DriftReport` (per-resource & per-field
   `compliant | drifted | unknown`, plus the reconcile action that would converge each, with an
   aggregate status + drift count). The connector port gains `evaluate_compliance(request) ->
   DriftReport`; simulation adapters produce believable, seeded, deterministic drift.

3. **Compliance-mode run** (M25.3) — any template/workflow can run in *compliance mode*: a dry-run
   that aggregates DriftReports (+ blast radius from M24) and **never mutates**. Scheduled sweeps
   (M25.4, reusing M11) snapshot posture and open incidents (M16) on drift.

`IdempotencyClass` lives in the **shared kernel** because it is a small, stable primitive consumed
by both `connectors` and `automation_catalog` (neither owns it; cross-context reach-in is forbidden).

## Consequences

**Good**
- The idempotency mandate becomes a *contract* the platform can show and check, not a hope.
- Drift is a first-class, deterministic signal that powers compliance dashboards, pinning (M27),
  and incidents — "assert desired state", not just "run things".
- Auto-classification means every existing connector action gets a class for free.

**Bad / costs**
- Name-based inference is a heuristic; a genuinely idempotent "delete" would be mis-flagged unless
  the adapter sets the class explicitly (acceptable — explicit override exists).
- Simulated drift must be carefully seeded to stay believable and deterministic.

## Alternatives considered
- **A boolean `idempotent` flag** — rejected: can't distinguish read-only/plan actions (check-only)
  from convergent mutations, which matters for compliance-mode semantics.
- **Per-adapter explicit classes only** — rejected as the *sole* mechanism: too much boilerplate and
  drift risk; inference-with-override is lower-effort and still correct.

# Personas — who does what

Nexus serves four roles over one shared domain. Each works at a different altitude.

## Automation engineer (authors atomic blocks)
**Goal:** deliver precise, consistent, low-effort automation capabilities.
- Authors **atomic building blocks** (catalog templates): connector + action + survey schema.
- Declares each block's **idempotency class**, **plain-language summary** (input → action → outcome
  + rollback), target **CI type**, and **risk**.
- Maintains **CMDB type schemas + lineage** (CMDB Schema Studio) — what a healthy CI must contain.
- Surfaces: Catalog (authoring/approval), CMDB Schema Studio, Connectors registry (Admin).

## Operator / engineer (composes & runs)
**Goal:** get governed work done without touching every backend.
- **Composes** vetted blocks on the **Canvas** into workflows (incl. sub-workflows); picks catalog
  items and saved/approved workflows as canvas pieces.
- **Runs** safely: dry-run / **compliance mode** first; live runs are gated by policy.
- **Recovers**: failed runs and drift become **incidents** to triage and remediate.
- Surfaces: Catalog, Canvas, Library, Console, Incidents, Compliance.

## Reviewer / executive (approves)
**Goal:** authorize change at the right level, in language they understand.
- Reviews a **Change Review Packet** with a **Technical / Non-technical / Executive** toggle —
  executives read plain outcomes + risk + rollback + a flowchart, never connector/param noise.
- Approves / rejects / requests changes from the **Approvals** queue; gated runs only proceed on
  approval. High-risk / prod / large-blast changes auto-escalate to executive review.
- Surfaces: Approvals, Governance.

## Admin / integrator (governs the platform)
**Goal:** make guarantees real and keep the platform healthy.
- Defines **deterministic pinning rules** (Guardrails) — guarantee a workflow for a class of CIs —
  and reads **coverage** ("what's guaranteed, where reality differs").
- Tunes the **validation policy** and **review policy**; manages **schedules** and **change control**.
- Operates the **GitOps** config backbone (back up / history / diff / restore) and reviews
  **compliance posture**.
- Surfaces: Admin, Determinism/Guardrails, GitOps, Compliance, Governance, Accessibility/Theme Studio.

See the [feature guides](../guides/surfaces.md) for how to use each surface.

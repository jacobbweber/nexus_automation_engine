# ADR-0011 — Multi-audience review & run-level approval

**Status:** Accepted (2026-06-20)

## Context

Governance must be real for **non-technical and executive** approvers, not just engineers. The
operator's requirement ([vision](../00_foundation/vision_deterministic_governance.md) §4): a human
must approve workflows *set to run* (not only CI adds); review must be tailored to the audience —
technical, non-technical, executive — translating Terraform/Ansible/JSON into plain outcomes; and
review depth should scale with the change (normal vs standard vs emergency).

The constraint: **no in-product AI** ([ADR-0008](./ADR-0008-no-in-product-ai.md)). So the
"translation" to plain language must be deterministic.

## Decision

A new bounded context **`review`** owns three things, all deterministic:

1. **Change classification** — `classify(ctx) → standard | normal | emergency` from risk + blast
   radius (M24) + target environment + idempotency class (M25); a tunable `ReviewPolicy` maps each
   class to a required reviewer level (`none | team_lead | executive`), escalating to executive on
   high/critical risk or large blast radius.

2. **The Change Review Packet** — a deterministic, multi-representation render of a workflow:
   **technical** (per step: connector/action/resolved params + idempotency), **non-technical /
   executive** (a plain narrative composed from each building block's authored `plain_summary`
   — `input → action → outcome` — in execution order, plus risk/outcome/rollback), and a
   **flowchart** phase list. The enabling move is requiring building blocks to carry a `plain_summary`
   (M26.1): the automation team authors intent in plain English **once**, and every workflow built
   from those blocks gets free, executive-ready review prose. No AI — composition only.

3. **Run-level approval gate** — a run the policy deems review-worthy enters a persisted
   `ApprovalRequest` (carrying a packet snapshot) and is **blocked** in `CanvasService.start_run`
   until approved; plan/compliance runs are exempt (read-only). Adding/modifying a CI takes the same
   path, gated on its CMDB health (M24).

The frontend renders the packet with a **Technical / Non-technical / Executive** toggle and an
approvals queue (approve / reject / request-changes).

## Consequences

**Good**
- Managers approve *plain outcomes* with a flowchart, never connector/param noise — governance that
  non-technical stakeholders can actually exercise.
- Review depth is proportional and deterministic; high-risk/prod/large-blast changes auto-escalate.
- Authoring the plain summary once yields packets for every composing workflow — high capability,
  low recurring effort.

**Bad / costs**
- Plain summaries are authored (seeded deterministically here) — quality depends on the author.
- A distinct **executive RBAC role** is deferred (a security-model change, per the standing J41
  decision); today the *executive view* is delivered via the packet toggle, and any authenticated
  reviewer can decide. Routing decisions to specific role-holders is a follow-up.

## Alternatives considered
- **LLM-generated plain-language summaries** — rejected (ADR-0008): non-deterministic and unsafe as
  a governance artifact. Authored-once + composition is deterministic and auditable.
- **Approve only at the change-management layer (2.0)** — insufficient: that gates *change records*,
  not the audience-tailored *run packet*; the two compose (a gated run can still stamp a CHG).

# Nexus 2.0 — Objective Review & Vision (ops-engineering / DevOps pass)

After 1.0 (a working control plane), this is the deliberate review from **both** sides of the
product: the automation engineer who *builds, governs, and maintains* the platform, and the
operator who *uses* it. The reframing that drives 2.0:

> **Nexus is a complete management layer.** Operations administers the *process* up front —
> change control, scheduling, approvals, policy — and Nexus automates the backend and logistical
> details. Operators stop being ticket-routers and become process owners; engineers stop
> hand-holding runs and instead encode policy once.

## What 1.0 proved, and where it stops short

1.0 lets you compose and run governed automation with live feedback. But a real enterprise ops
team needs the *process wrapper* around execution: change management, scheduling/windows, deeper
approval policy, and the tooling to operate the platform itself. That wrapper is 2.0.

## 2.0 themes (prioritized)

### A. Change control as a first-class concern  ⭐ flagship (M10)
- Per-job / per-workflow **"automatic change control"** toggle.
- A **standard Change Template**: a reusable bundle of change fields (assignment group, risk,
  impact, category, description, CAB-required) bound to a job/workflow.
- On execution, Nexus auto-creates/associates a **Change Record** (ServiceNow-style) and stamps
  the change number onto the run — closing it out on completion/failure. Fully configurable;
  enforce "no production mutation without an approved change."
- *Why it's a massive win:* it turns ad-hoc automation into audited, governed change — the single
  biggest blocker to letting operators self-serve against production.

### B. Scheduling & windows  (M11)
- Schedule a job/workflow: one-off or recurring (cron/interval), with inputs.
- **Maintenance windows** and **blackout windows**; change-calendar awareness; "run only inside
  an approved window."
- A background scheduler that claims due schedules (pull model, like the harvested Ava pattern).

### C. Approval & policy depth  (M12)
- Multi-stage approvals, approver roles, separation-of-duties.
- **Policy-as-config**: which flows require change control / approval / a window, by environment
  or asset group. Engineers write policy once; it applies everywhere.

### D. Operator self-service maturity
- Flow **blueprints/templates** operators clone; parameter **presets**; saved targets; a runbook
  framing over workflows.

### E. Platform builder/maintainer experience
- Connector **SDK + registry/marketplace** surface; capability-schema-driven node forms so new
  connectors self-describe; connector **health/diagnostics**; audit & compliance **export**;
  observability of the platform itself.

### F. Cross-functional value
- Plan/dry-run everywhere, **drift detection** surfacing, blast-radius preview, environment
  **promotion** flows, notifications/webhooks, RBAC reporting.

## Delivery shape

2.0 is delivered as milestones M10+ behind the same SDD/TDD discipline, each tagged
(`v1.x`) as it lands, with **`v2.0.0`** cut once change control + scheduling + policy depth (A–C)
and at least one of D/E are delivered and verified. New bounded contexts (`change_management`,
`scheduling`, `governance_policy`) follow the vertical-slice rules; they integrate with execution
and canvas only through published contracts.

See ADR-0005 (change management) and the roadmap status log.

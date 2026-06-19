# Feature Depth — Per-Surface Expansion

The deep-feature program for every Nexus surface, framed around the operator's five jobs (find,
understand, run, compose, recover) and the admin's governance jobs. Backend contexts already exist
for most of this (`orchestration_canvas`, `automation_catalog`, `connectors`,
`change_management`, `scheduling`, `incident_management`, `lifecycle_validation`,
`execution_engine`, `identity_access`); this spec is about the experience depth on top.

> **Cross-cutting primitives** every surface inherits: the ⌘K command palette ("find-and-run
> anything"), a non-blocking **notifications feed** (run finished / approval requested / incident
> opened), **global search**, keyboard-first navigation, calm **empty states** with a "set this up
> for me" shortcut, and honest **offline/degraded** states when a connector or container is down.

## Dashboard — operational overview

- **Fleet pulse**: running/queued/failed counts, success-rate and MTTR trends, change-window
  calendar peek, approvals-waiting, incidents-open — all drill-through.
- **"Needs attention" feed**: stale automations (from the review/pruning status), failing
  hotspots, pending approvals assigned to me, scheduled runs imminent.
- **My queue / recents / favorites**: personalized fast lanes into the catalog and library.
- **Live activity stream**: most recent runs with status badges, click → Console.

## Catalog — find & understand

- **Discovery at scale**: type-ahead + faceted filters (domain → vendor → capability, tags, risk
  tier, est. duration, owner), **collections**, favorites/recents, popularity + success-rate.
- **Atomic vs orchestrated** visually distinct; orchestrated items show phase count.
- **Automation detail**: README/markdown, parameter schema, prerequisites, **risk + est. duration
  + owner**, last-N runs + success rate, related CIs.
- **Logic-Flow tab**: animated SVG of the automation's phases/DAG that also animates the live
  execution trace node-by-node (the centerpiece "wow"; already seeded by 3.0).
- **Blast-radius preview**: which CMDB CIs/services a run would touch (impact analysis) before you
  commit.
- **Run-from-template wizard**: survey-driven, CMDB-backed target pickers, **dry-run/plan first**,
  saved **parameter presets / targets** ("prod-east fleet", "PCI hosts").
- **Comparison**: select 2–3 automations → side-by-side capabilities/risk/params.

## Canvas — compose (Lego)

- **Schema-driven nodes** (shipped, M19): typed parameters per node type rendered as guided
  controls; richer condition logic; CMDB field picker; dynamic output handles.
- **Comprehension aids**: minimap, auto-layout, fit-to-view, search-nodes, group/comment nodes.
- **Validation/lint**: cycle detection, unreachable nodes, missing-required-params, type mismatch,
  surfaced inline before save/run.
- **Dry-run / plan preview** + **blast-radius** overlay for the whole graph.
- **Live run overlay**: per-node status ring + inline log tail + timing; pause at approval gates.
- **Run replay / time-travel**: scrub a completed run's trace forward/back; inspect each node's
  inputs/outputs (secrets stay masked).
- **Versioning**: snapshot, list versions, **visual diff/compare** between versions.
- **Subgraph templates / reusable blocks**: promote a vetted subgraph into a reusable component;
  insert sub-workflows.
- **Run-inputs prompt** (shipped, M19): collect declared Start inputs at launch.

## Library — saved, governed, reported

- **Workflow library + reporting** (shipped, M19): owner/team/tags, usage telemetry (run count,
  success rate, last run), filter by team/tag, open in canvas.
- **Drill-down dashboards**: per-workflow run history, success-rate over time, MTTR, schedule
  links, incident links.
- **Lifecycle at a glance**: review state (draft → submitted → … → published) with quick actions.
- **Bulk operations**: tag, assign owner, archive, schedule.

## Console — run & observe

- **Live job stream** with ANSI rendering, auto-scroll + pin, `aria-live` for screen readers.
- **Log search/filter** within a run; jump to errors; download artifacts.
- **Run compare**: diff two runs of the same automation (params + outcome + timing).
- **Controls**: retry, cancel, re-run with same/edited params, resume at approval gate.
- **Step timeline**: per-step status, duration, retry count, inputs/outputs (masked secrets).

## Incidents — recover

- **Auto-capture kanban** (shipped): failed run/workflow → incident card (New → Triage →
  Investigating → Resolved), linked to the failing run + logs.
- **Convert incident → remediation workflow** on the canvas (shipped).
- **RCA assist**: "similar past failures", suggested remediations from prior resolutions, common
  failure-mode tagging.
- **Trends**: top failing automations, MTTR by domain, recurring-failure detection.

## Governance — control & review

- **Approvals inbox**: workflows submitted for review; approve/request-changes/reject with
  comments; review history as audit.
- **Change calendar**: change records (CHG) + scheduled runs + maintenance windows in one view;
  conflict detection.
- **Validation policy editor**: the single admin-editable `ValidationPolicy` (required fields, max
  review age, CMDB-consistency toggles, destructive-on-cluster block).
- **Pruning & review dashboard**: fresh/stale/never-reviewed automations + oldest, with bulk
  review actions.
- **Audit trail**: who ran/approved/changed what, exportable.

## Admin — access & identity

- **RBAC matrix editor**: roles (admin/engineer/operator/consumer) × capabilities, visual grid.
- **Users & entitlements**: manage principals, assign roles, scope entitlements.
- **Capability registry**: what each role can do; safe defaults; least-privilege hints.

## Platform / System — the control plane for the control plane

- **Connector registry + simulation controls**: list connectors, capabilities, toggle/inspect the
  simulation adapters, health per connector.
- **Resource & container view**: health of backend containers, run/queue depth, restart, logs;
  a "running locally, nothing leaves this machine" status banner.
- **Theme Studio + theme library** (see `02_theming.md`).
- **Accessibility center**: mode, theme, density, motion, dyslexia font, contrast, text-scale,
  keyboard map — plus a single "make this easier to use" guided setup.
- **Notifications & rules**, **command-palette config**, **backup / export** (portable JSON, no
  lock-in).

## Optional Assistant (local-model, off by default)

A forward-looking, **optional** local-model assist layer behind an adapter (same port pattern as
connectors; local only, no paid services). It augments — never gates — operator work:

- **Explain this failure** (summarize a run's logs + likely cause), **suggest remediation**
  (propose a remediation workflow from a failing incident), **draft a change record** from a
  workflow, **describe → workflow scaffold** (natural language to a draft canvas graph for the
  operator to refine), **summarize a long run**. Every output is a draft the operator reviews; the
  deterministic engine remains the source of truth.

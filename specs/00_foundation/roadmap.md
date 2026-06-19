# Roadmap — Nexus Automation Engine

Living delivery plan. Milestones map to **releases** (versions), not time-boxes
(`CLAUDE.md §7`). Built under full autonomy ([ADR-0003](../adr/ADR-0003-full-autonomy-to-2.0.md)).

---

## Road to 1.0 (the MVP defined in `.claude/project.md §3`)

Each milestone = one or more branches → TDD → green CI → merge. A milestone closing tags a
`0.x` release.

| # | Milestone | Delivers | Target tag |
| --- | --- | --- | --- |
| M1 | **Platform & slice skeleton** | FastAPI app + async SQLite WAL helper + config + security middleware seam; `shared_kernel` (ids, errors, `VariablePool`); context package scaffolding; React/Vite/TS/Tailwind/Radix shell; real `$LINT_CMD`/`$TEST_CMD` wired into CI. | `v0.1.0` |
| M2 | **Connectors** | `ExecutionConnector` + `DiscoveryPort`/`SecretLeasePort`/`ApprovalPort`/`TelemetryPort`; **simulation adapters** (Ansible/Terraform/script) with ANSI + jitter streaming; ServiceNow/CyberArk/Dynatrace sim adapters; connector **contract tests**. | `v0.2.0` |
| M3 | **Execution engine** | Job lifecycle state machine (PENDING→RUNNING→SUCCESS/FAILED/CANCELLED); asyncio worker queue; WS log streaming; telemetry endpoint; seeded 50+ historical runs. | `v0.3.0` |
| M4 | **Identity & access** | Users/orgs/teams; JWT auth; RBAC entitlement evaluation down Org→Team→AssetGroup; login. | `v0.4.0` |
| M5 | **Automation catalog** | Unified runner templates; survey-field schema + renderer contract; ownership & approval state of building blocks. | `v0.5.0` |
| M6 | **Canvas backend** | Full DAG engine (VariablePool, parallel exec, skip propagation, retries/error edges); all generic + backend-integration node types; workflow/version/run persistence; approval resume; WS frames. | `v0.6.0` |
| M7 | **Canvas UI** | Pan/zoom canvas, palette, port connections, colored handles, properties panel + connector dropdown, ANSI run terminal, approval overlay, history. | `v0.7.0` |
| M8 | **Frontend surfaces** | Dashboard, catalog, job console (Terraform/Ansible split panes + telemetry pane), admin/settings. | `v0.8.0` |
| M9 | **Containerization & QA** | Multi-stage rootless Dockerfile; docker-compose; container/QA smoke; behavioral evals; polish. Then cut **`v1.0.0`** once `$ONE_POINT_OH` holds. | `v1.0.0` |

## Road to 2.0 — the ops-engineering / DevOps cross-functional pass

After 1.0, do a full objective review and push to 2.0, designing from **both** the automation
engineer (building/managing/maintaining the platform) and operator (using it) perspectives. The
framing: **Nexus as a complete management layer** — ops admins the *process* up front; Nexus
automates the backend and logistical details. Seeded themes (expand during the 2.0 pass):

- **Change control as a first-class concern.** Per-job toggle for **"automatic change control"**;
  a **standard Change Template ID + fields** bound to a job/workflow; create/associate
  ServiceNow (or generic ITSM) change records automatically on execution. Configurable per job.
- **Scheduling.** **Schedule changes per job/workflow** (one-off and recurring), with maintenance
  windows, blackout windows, and change-calendar awareness — configurable.
- **Approval & policy depth.** Multi-stage approvals, approver roles, policy-as-config (which
  flows require change control / approval / a window), separation-of-duties.
- **Operator self-service maturity.** Flow templates/blueprints operators can clone; parameter
  presets; "run book" framing; saved targets.
- **Platform builder/maintainer experience.** Connector SDK + connector registry/marketplace
  surface; capability-schema-driven node forms so new connectors self-describe; health/diagnostics
  for connectors; audit & compliance export; observability of the platform itself.
- **Cross-functional value.** Dry-run/plan-everywhere, drift detection surfacing, blast-radius
  preview, environment promotion flows, notifications/webhooks, RBAC reporting.

These are captured as GitHub issues under a `2.0` milestone during the 2.0 pass and refined into
context specs before building (SDD).

## Status log
- Foundation specs + CI runner: **done** (merged).
- M1 (platform & slice skeleton): **done** — released **v0.1.0**.
- M2 (connectors): **done** — ports + simulation adapters + registry + API.
- M3 (execution engine): **done** — lifecycle state machine, WS log streaming, telemetry, seed.
- M4 (identity & access): **done** — RBAC model + entitlements, JWT auth, login/me/users, seeded users.
- M5 (automation catalog): **done** — templates/surveys/approval + execute-from-template.
- M6 (canvas backend): **done** — DAG engine, 15 node types, approval gates, persistence, WS.
- M7 (canvas UI) + M8 (frontend surfaces): **done** — auth, dashboard, catalog, console (live WS),
  admin, and the visual canvas (palette, connect, connector dropdown, run highlight, approval).
- M9 (containerization & QA): **done** — rootless Dockerfile + compose; live end-to-end server
  smoke passed (auth, seeded data, canvas run). **Released v1.0.0.**
- **1.0 reached.** Next: the 2.0 ops-engineering pass (change control, change templates, per-job
  scheduling, platform-as-management-layer).

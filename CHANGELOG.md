# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses Semantic Versioning.

## [Unreleased]

### Changed
- **Audit B1 — static typing**: adopted **mypy** in CI (clean across 125 files). Fixed real type
  issues found along the way and renamed shadowing `list()` repository/service methods to
  `list_all()`.
- **Audit Q2 — de-dup**: extracted the duplicated live-broadcast broker into a shared-kernel
  `AsyncBroker`; the execution and canvas brokers are now thin singletons over it.
- **Audit B2 — hardened gate**: enabled ruff **`S` (flake8-bandit) security rules** (with
  documented exceptions; the reviewed `eval` is annotated and the lone `assert` replaced by a
  guard), and added **test coverage** reporting to CI (91% at adoption).

### Fixed
- **Audit A1 — crash recovery**: a startup recovery sweep marks orphaned PENDING/RUNNING jobs and
  RUNNING workflow runs as FAILED after a restart, so persisted state stays honest. Documented the
  single-instance ceiling.

### Added
- **M18 CMDB Lifecycle Validation** ("origin-story validation", `lifecycle_validation` context,
  ADR-0006): every automation must carry required metadata (authored_by, approved/updated/reviewed
  dates, CI type + heritage) and pass a **CMDB CI-lifecycle consistency check** before it runs.
  Rejects runs whose target contradicts the CMDB — retired CIs, CI-type mismatches, unknown CIs,
  and **destructive actions on cluster-member datastores**. Governed by a **single admin-editable
  `ValidationPolicy`** every execution consults. The simulated CMDB gained CI type / lifecycle /
  cluster data; catalog items carry the metadata; approval stamps the review date. New
  `/governance/validation/policy|check|review-status` endpoints + a **pruning/review dashboard**
  (fresh / stale / never-reviewed + oldest). 119 backend tests.

### Security
- **Gate now covers canvas `automation_task` nodes** (single-target ops) in addition to catalog +
  direct-job paths; added an advisory `npm audit` step to CI.
- **Audit S2 — login throttling**: repeated failed logins are rate-limited (5 failures / 5 min
  per username → 429; cleared on success).
- **Central gate extended**: the `/api/v1/jobs/execute` direct path now also runs the CMDB
  lifecycle-consistency gate on its target (ad-hoc jobs to retired/cluster/unknown CIs are
  rejected) — not just catalog runs.
- **Audit S3 hardening**: security-response headers (CSP, `nosniff`, frame-deny, referrer) + a
  request body-size limit (413), and an **SSRF guard** on the `http_request` canvas node that
  blocks loopback/private/link-local/cloud-metadata targets (override via `NEXUS_HTTP_ALLOW_PRIVATE`).
- **Audit S1/S2 fixes**: job execution, queries, telemetry, and canvas run now **require
  authentication**; live-vs-check execution is **entitlement-checked**; the auditable
  `initiated_by` is **derived from the token** (client-supplied executor is ignored — anti-spoof);
  and the app **refuses to boot** a non-local/test environment on the default JWT secret. Tests
  cover unauth rejection + anti-spoof. (Remaining S-items tracked in the audit doc.)

### Added
- **Four formal audit reports** (`specs/audits/`): security & compliance, code quality,
  architecture/scalability/performance, and best-practice/linting/maturity — each with rated
  findings, a remediation plan, and a checklist, plus a consolidated remediation order.
- **M16 Incident / Error Kanban** (`incident_management` context): failed jobs **and** workflow
  runs auto-open an **incident card** (de-duplicated per source) on a triage board
  (New → Triage → Investigating → Resolved). Move cards, and **convert an incident → a draft
  remediation workflow** on the canvas (one click). `/api/v1/incidents/board|move|remediate` +
  a frontend kanban board. 107 backend tests.
- **M15 Governed workflow submission & review**: operators **submit** a composed workflow for
  review; engineers/admins **approve / request changes / reject** with comments via a Governance
  **review inbox**. Workflows carry a `review_state` (draft→submitted→…→approved/published) and a
  full review audit trail; graph edits preserve review state. Canvas gains a "Submit for review"
  action. `/api/v1/canvas/workflows/{id}/submit|review`, `/canvas/reviews/pending`. 100 tests.
- **M14 Catalog-at-scale UX** (`frontend/`): a faceted Service Catalog (domain/vendor facets with
  counts + type-ahead search, grouped cards with risk pills and atomic/orchestrated badges) and an
  **automation detail drawer** with tabs — Overview (rendered Markdown docs + prerequisites +
  tags), Parameters, and an **animated Logic-Flow SVG** of the automation's phases. Reusable
  `Markdown` + `LogicFlow` components.

- **3.0 operator-experience vision** (`specs/00_foundation/vision_operator_experience.md`): a
  fresh from-the-operator rethink — service catalog at scale, understand-before-you-run,
  governed Lego composition, incident kanban, and a believable large catalog.
- **M13 Connector ecosystem + rich catalog**: new simulation connectors **VMware (VCF 9)**,
  **Pure Storage (FlashArray)**, and **Cohesity** (each with realistic actions + streamed logs);
  catalog templates gained operator metadata (**domain, vendor, tags, risk tier, est. duration,
  prerequisites, version, atomic/orchestrated**); faceted list filtering (`domain`/`vendor`/
  `search`) + `/catalog/facets`; and a **27-item multi-vendor seed catalog** (VCF, Pure,
  Cohesity, ServiceNow-via-Ansible, Ansible, Terraform, scripts) where every item runs. 95 tests.

### Changed
- **CI hardening**: `runs-on: self-hosted` (drop the custom label so a vanished runner label can't
  hang CI), plus `PYTHONDONTWRITEBYTECODE` + `pytest -p no:cacheprovider` so the runner workspace
  stays clean for `actions/checkout`.

## [2.0.0] - 2026-06-18

The **ops-engineering management layer**: Nexus 2.0 wraps execution in governed change and
scheduling, so operations administers the *process* up front and Nexus automates the rest. Driven
by the objective review in `specs/00_foundation/vision_2_0.md`.

### Added
- **Change Management** (M10, `change_management` context, ADR-0005): reusable change templates
  (standard ITSM fields + CAB flag), per-resource change-control policies (`auto_change_control`,
  `change_template_id`, `require_approved_change`), and change records (CHG numbers + lifecycle).
  The catalog execute path opens a change per policy and stamps the change number onto the job;
  CAB-required changes block live runs until approved. `/api/v1/change` (engineer-gated). Jobs
  gained an optional `change_number`.
- **Scheduling** (M11, `scheduling` context): schedule workflows on interval or daily triggers
  with optional **maintenance windows**; a background ticker dispatches due schedules through the
  canvas. `/api/v1/schedules` CRUD + run-now.
- **Governance UI** (M12): a frontend Governance surface for change templates, change records
  (audit table), and schedules (create/run/delete).
- 88 backend tests; full backend + frontend CI green.

### Notes
- Continuing on the roadmap beyond 2.0: deeper policy-as-config (theme C), platform-builder /
  connector-SDK UX (E), and cross-functional features — drift, promotion, notifications (F).

## [1.0.0] - 2026-06-18

The MVP (`$ONE_POINT_OH`): a working, simulation-backed Automation Control Plane an operator can
authenticate to, browse, compose on a visual canvas, and run end-to-end with live logs and
governance — verified against a live server. Built as DDD vertical slices across six bounded
contexts with a self-hosted CI gate.

### Added
- **Connectors** (M2): vendor-agnostic ports (`ExecutionConnector`, `DiscoveryPort`,
  `SecretLeasePort`, `ApprovalPort`, `TelemetryPort`) + simulation adapters for
  Ansible/Terraform/script and ServiceNow/CyberArk/Dynatrace, a registry, and the `/connectors`
  API that powers the canvas connector dropdown.
- **Execution engine** (M3): job lifecycle state machine, persisted runs + log streams,
  in-memory broker + `WS /jobs/{id}/stream` (with replay), telemetry endpoint, and 50+ seeded
  historical runs.
- **Identity & Access** (M4): users/orgs/teams RBAC with capability matrix + entitlement
  evaluation, PBKDF2 + JWT auth (no native deps), `auth/login|me|users`, seeded demo users.
- **Automation Catalog** (M5): governed building blocks — templates, survey schemas, approval
  lifecycle, and execute-from-template (RBAC-checked).
- **Orchestration Canvas** (M6): the ported Foundry DAG engine re-targeted to connectors —
  parallel execution, condition/switch routing with skip propagation, per-node retries and error
  branches, approval gates (pause/resume), 15 node types incl. all backend-integration nodes,
  workflow/version/run persistence, and `WS` run streaming.
- **Frontend** (M7/M8): JWT auth, dashboard, catalog (+execute), live-streaming console, admin,
  and the visual canvas (pan/zoom, palette, port connections, connector dropdown, run
  highlighting, approval overlay).
- **Containerization** (M9): multi-stage rootless `Dockerfile` (single container serving SPA +
  API), `docker-compose.yml`, and the project README.

### Notes
- Pre-1.0 foundations (specs, DDD architecture, CI runner, platform skeleton) shipped in 0.1.0.
- Deferred to post-1.0: remaining canvas source node types (iterator/code/llm/tool/knowledge —
  issue #19) and live container-image build verification (Docker Desktop daemon flakiness).

## [0.1.0] - 2026-06-18

First tagged milestone (M1): foundation specs (DDD vertical slices + Canvas Orchestration), the
self-hosted CI gate, the backend platform skeleton (FastAPI + WAL SQLite + `shared_kernel` /
VariablePool), and the React/Vite/Tailwind frontend shell. See ADRs 0001–0004.

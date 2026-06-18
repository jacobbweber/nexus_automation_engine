# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses Semantic Versioning
(pre-1.0 `0.x` line — breaking changes permitted within MINOR).

## [Unreleased]

### Added
- **M5 Automation Catalog** (`backend/app/contexts/automation_catalog/`): governed building
  blocks — templates with survey-field schemas (incl. CMDB-backed dynamic pickers), ownership,
  and a draft→pending→approved→retired lifecycle. `GET /api/v1/catalog/templates[/{id}]`,
  engineer-gated author/approve/retire, and **execute-from-template** that maps survey answers to
  a connector ExecutionRequest and dispatches a governed job (RBAC-checked). Seeded building
  blocks. 58 backend tests total.
- **M4 Identity & Access** (`backend/app/contexts/identity_access/`): users/orgs/teams/asset-groups
  RBAC model with the global-role capability matrix and pure entitlement evaluation
  (Org→Team→AssetGroup); PBKDF2 password hashing + JWT (no native deps); `POST /api/v1/auth/login`,
  `GET /auth/me`, `GET /auth/users` (admin-only) with bearer/role dependencies; default users
  seeded on startup. 51 backend tests total.
- **M3 Execution engine** (`backend/app/contexts/execution_engine/`): the job lifecycle state
  machine (PENDING→RUNNING→SUCCESS/FAILED/CANCELLED) driven by the connector ports. Persists jobs
  + log streams (SQLite/WAL), broadcasts live logs over an in-memory broker to a
  `WS /api/v1/jobs/{id}/stream` endpoint (with persisted-log replay), plus
  `POST /jobs/execute`, `GET /jobs[/{id}][/logs]`, and `GET /telemetry/{job_id}`. Seeds 50+
  realistic historical runs on startup. Service/repository/API/WS tests (42 backend tests total).
- **M2 Connectors context** (`backend/app/contexts/connectors/`): the vendor-agnostic
  Anti-Corruption Layer. Vendor-neutral domain models + ports (`ExecutionConnector`,
  `DiscoveryPort`, `SecretLeasePort`, `ApprovalPort`, `TelemetryPort`); simulation adapters for
  Ansible / Terraform / script (streaming ANSI logs, check/diff mode, failure paths) and
  ServiceNow (CMDB discovery + request approval) / CyberArk (secret lease) / Dynatrace
  (telemetry); a connector registry; and `GET /api/v1/connectors[/{kind}]` + CMDB discovery
  endpoint that power the canvas node connector dropdown. Contract + behavioral tests (31 total).

## [0.1.0] - 2026-06-18

First tagged milestone (M1): the foundation and platform skeleton are in place and CI enforces
real backend + frontend checks on the self-hosted runner.

### Added
- **CI & runner**: self-hosted GitHub Actions runner (`[self-hosted, nexus]`) and the CI gate
  (`.github/workflows/ci.yml`) — runner smoke, backend lint+tests, frontend lint+types+tests+build.
- **Foundation specs** (`specs/`): spec conventions, DDD vertical-slice architecture, living
  glossary, the delivery roadmap (M1–M9 to 1.0 + the 2.0 ops-engineering themes), and the
  **Canvas Orchestration spec** — full port of the Ava-POC Foundry DAG/canvas, re-targeted to
  backend connectors.
- **Project Profile** (`.claude/project.md`) defining all `CLAUDE.md` variables and the concrete
  1.0 definition.
- **ADRs**: 0001 (DDD + Vertical Slices), 0002 (port the Foundry canvas), 0003 (full autonomy to
  2.0), 0004 (synchronous SQLAlchemy).
- **Backend platform skeleton** (`backend/`): FastAPI app factory + `/api/v1/health`, config,
  the single WAL-mode SQLite DB helper, error-to-HTTP mapping, and the `shared_kernel`
  (`new_id`, error types, and the ported **VariablePool**). Full pytest + ruff suite.
- **Frontend shell** (`frontend/`): React 18 + Vite 6 + TypeScript + Tailwind v4 with the Nexus
  design tokens, an `AppShell` nav frame mirroring the feature slices, a typed API client, and a
  live backend-health indicator. ESLint + tsc + Vitest + build.

### Changed
- `CLAUDE.md`: added DDD + Vertical Slices as a standing architecture directive (§4a); replaced
  the gated autonomy boundary with full autonomous delivery to 2.0 (§2, per ADR-0003).

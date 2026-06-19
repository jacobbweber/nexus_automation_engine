# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses Semantic Versioning.

## [Unreleased]

_Nothing yet._

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

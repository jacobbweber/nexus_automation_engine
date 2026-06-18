# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses Semantic Versioning
(pre-1.0 `0.x` line — breaking changes permitted within MINOR).

## [Unreleased]

### Added
- **M1 backend platform skeleton** (`backend/`): FastAPI app factory with `/api/v1/health`,
  config (pydantic-settings), the single WAL-mode SQLite DB helper, error-to-HTTP mapping, and
  the `shared_kernel` (`new_id`, error types, and the ported **VariablePool** with typed
  exact-replacement, safe expression eval, and Jinja2-lite templating). Full pytest + ruff suite.
- CI now runs real backend lint + tests (replacing the stub jobs); ADR-0004 records the switch
  to synchronous SQLAlchemy (greenlet is blocked by Application Control on the dev/CI host).

- Self-hosted GitHub Actions runner and initial CI gate
  (`.github/workflows/ci.yml`): runner smoke test plus stubbed lint/test stages on the
  `[self-hosted, nexus]` runner.
- Project Profile (`.claude/project.md`) defining all `CLAUDE.md` variables, the source layout,
  constraints, and the concrete 1.0 definition.
- Foundation specs: spec conventions, DDD vertical-slice architecture, and the living glossary
  (`specs/00_foundation/`).
- Canvas Orchestration spec (`specs/02_canvas_orchestration/canvas_orchestration.md`) — the
  full port of the Ava-POC Foundry DAG/canvas feature, re-targeted to backend orchestration
  (connector-bound nodes for Ansible/Terraform/script + ServiceNow/CyberArk/Dynatrace).
- ADR-0001 (DDD + Vertical Slices) and ADR-0002 (port the Foundry canvas as the orchestration
  core) under `specs/adr/`.

### Changed
- `CLAUDE.md`: added Domain-Driven Design + Vertical Slices as a standing architecture
  methodology directive (§4a) alongside SDD/TDD.
- `CLAUDE.md §2`: replaced the gated autonomy boundary with **full autonomous delivery to 2.0**
  (no approval gates; judgment guardrails instead) per operator mandate (ADR-0003).

### Added
- ADR-0003 (full autonomy to 2.0) and the delivery `specs/00_foundation/roadmap.md`
  (M1–M9 to 1.0, plus the 2.0 ops-engineering theme set: change control, change templates,
  per-job scheduling, platform-as-management-layer).

# Nexus Automation Engine

A unified, **vendor- and platform-agnostic Automation Control Plane**. Nexus puts one simple,
secure, governed front end over dispersed backend automation systems (Ansible AAP, Terraform,
PowerShell/Python jump-box executors) and enterprise systems of record (ServiceNow, CyberArk,
Dynatrace). Automation engineers govern *what can run*; operators compose and execute their own
flows from approved building blocks on a **visual orchestration canvas** — and every change is
schema-checked, idempotent, human-reviewed, and versioned in Git.

> North star: **build it once, govern it centrally, let anyone run it safely.**

## 📸 See it in action → [**SHOWCASE.md**](SHOWCASE.md)

A scrollable, screenshot-driven tour of every major surface — what each is for, how it helps, in
3–4 bullets. Start there if you want the picture before the prose.

## Highlights

- **Visual Orchestration Canvas** — drag nodes, bind each to a backend via a connector
  (Ansible / Terraform / scripts / ServiceNow CMDB / CyberArk / Dynatrace), add conditions, approval
  gates, retries; **dry-run** the whole DAG or run it with live streamed logs.
- **Governed self-service** — RBAC (Org → Team → AssetGroup), a catalog of approved atomic building
  blocks, and **multi-audience review** (technical / non-technical / executive) with a run-level
  approval gate — operators stay inside guardrails engineers define.
- **Absolute configuration management** — the CMDB is a **schema-enforced contract** with
  deterministic health & lineage; all automation declares an **idempotency class** and is
  continuously re-runnable to prove **compliance** (drift → posture → incidents).
- **Determinism by policy** — **pinning rules** guarantee a workflow per class of CI, with a coverage
  view of where reality doesn't match desired state.
- **GitOps backbone** — the platform versions its own configuration in local Git (history / diff /
  restore / backup / pull-preview).
- **No in-product AI** — every "smart" output is computed deterministically
  ([ADR-0008](specs/adr/ADR-0008-no-in-product-ai.md)).
- **Alive in simulation** — a stateful simulation layer streams realistic ANSI logs, drives the job
  lifecycle, and seeds a lived-in history, so the whole system is demonstrable without real backends.

## Architecture

Domain-Driven Design organized as **vertical slices** (bounded contexts), each owning its full stack
(domain → application → infrastructure → api). See
[`specs/00_foundation/architecture.md`](specs/00_foundation/architecture.md).

- **Backend** — Python 3.11+ · FastAPI · SQLAlchemy 2.0 (SQLite/WAL) · synchronous DB
  ([ADR-0004](specs/adr/ADR-0004-synchronous-sqlalchemy.md)). Bounded contexts include
  `orchestration_canvas`, `catalog`, `execution`, `identity`, `connectors`, `change`, `scheduling`,
  `incidents`, `cmdb`, `compliance`, `review`, `determinism`, `gitops`.
- **Frontend** — React 18 · Vite · TypeScript · Tailwind v4.

## Run it

### Docker (single container: API + SPA)

```bash
docker compose up --build
# open http://localhost:8000
```

### Local development

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m uvicorn app.main:app --app-dir . --reload   # :8000

# Frontend
cd frontend
npm install && npm run dev   # :5173 (proxies /api to :8000)
```

**Demo users** (seeded): `admin` / `engineer` / `operator` / `consumer` — password is the username +
`123` (e.g. `operator123`). Dev-only.

The interactive API docs (Swagger / ReDoc) are served at **`/api-docs`** and **`/api-redoc`**
(relocated off `/docs`, which is the app's own in-product documentation surface).

## Testing

```bash
cd backend && .venv/Scripts/python -m pytest && .venv/Scripts/python -m ruff check .
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
```

CI runs all of the above on a self-hosted runner for every PR (`.github/workflows/ci.yml`).

## Documentation & Specs

### Product documentation ([`docs/`](docs/)) — also served in-app at `/docs`
- [Docs home](docs/README.md)
- **Concepts** — [Atomic automation → governed composition](docs/concepts/atomic-automation.md) ·
  [The determinism & idempotency mandate](docs/concepts/determinism-mandate.md)
- **Personas** — [Who does what](docs/personas/personas.md)
- **Guides** — [Feature guides, by surface](docs/guides/surfaces.md)
- **Strategy** — [Infracode pillar-repo strategy](docs/strategy/infracode-repos.md)

### Foundation specs ([`specs/00_foundation/`](specs/00_foundation/))
- [Architecture](specs/00_foundation/architecture.md) ·
  [Glossary](specs/00_foundation/glossary.md) ·
  [Roadmap](specs/00_foundation/roadmap.md) ·
  [Spec conventions](specs/00_foundation/_conventions.md)
- Vision: [2.0 (ops-engineering)](specs/00_foundation/vision_2_0.md) ·
  [3.0 (operator experience)](specs/00_foundation/vision_operator_experience.md) ·
  [4.0 (Deterministic Governance)](specs/00_foundation/vision_deterministic_governance.md)

### Domain specs
- [Canvas Orchestration](specs/02_canvas_orchestration/canvas_orchestration.md)
- [CMDB Schema & Lineage](specs/07_cmdb/cmdb.md)
- Experience: [Overview](specs/05_experience/00_overview.md) ·
  [Design System](specs/05_experience/01_design_system.md) ·
  [Theming](specs/05_experience/02_theming.md) ·
  [Feature Depth](specs/05_experience/03_feature_depth.md) ·
  [Roadmap](specs/05_experience/04_roadmap.md)

### Architecture Decision Records ([`specs/adr/`](specs/adr/))
| ADR | Decision |
| --- | --- |
| [0001](specs/adr/ADR-0001-ddd-vertical-slice-architecture.md) | DDD organized as vertical slices |
| [0002](specs/adr/ADR-0002-port-foundry-canvas-as-orchestration-core.md) | Canvas as the orchestration core |
| [0003](specs/adr/ADR-0003-full-autonomy-to-2.0.md) | Full autonomous delivery (no approval gates) |
| [0004](specs/adr/ADR-0004-synchronous-sqlalchemy.md) | Synchronous SQLAlchemy |
| [0005](specs/adr/ADR-0005-change-management.md) | Change management bounded context |
| [0006](specs/adr/ADR-0006-lifecycle-validation-gate.md) | Lifecycle validation gate |
| [0007](specs/adr/ADR-0007-experience-and-theming-architecture.md) | Experience & theming architecture |
| [0008](specs/adr/ADR-0008-no-in-product-ai.md) | No in-product AI/LLM |
| [0009](specs/adr/ADR-0009-cmdb-schema-and-lineage-context.md) | CMDB schema & lineage context |
| [0010](specs/adr/ADR-0010-idempotency-and-compliance-model.md) | Idempotency & compliance model |
| [0011](specs/adr/ADR-0011-multi-audience-review-and-run-approval.md) | Multi-audience review & run approval |
| [0012](specs/adr/ADR-0012-deterministic-pinning-reconcile.md) | Deterministic pinning & reconcile |
| [0013](specs/adr/ADR-0013-gitops-config-backbone.md) | GitOps config backbone |

### Audits ([`specs/audits/`](specs/audits/))
[Security & Compliance](specs/audits/01_security_and_compliance.md) ·
[Code Quality](specs/audits/02_code_quality.md) ·
[Architecture, Scalability & Performance](specs/audits/03_architecture_scalability_performance.md) ·
[Best-Practice, Linting & Maturity](specs/audits/04_best_practice_linting_maturity.md)

## Status

**`v4.0.0` — Deterministic Governance** (latest release). See [`CHANGELOG.md`](CHANGELOG.md) and the
delivery [`roadmap`](specs/00_foundation/roadmap.md). The agent operating manual is
[`CLAUDE.md`](CLAUDE.md); project specifics live in [`.claude/project.md`](.claude/project.md).

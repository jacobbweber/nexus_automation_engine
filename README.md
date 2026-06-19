# Nexus Automation Engine

A unified, **vendor- and platform-agnostic Automation Control Plane**. Nexus puts one simple,
secure, governed front end over dispersed backend automation systems (Ansible AAP, Terraform,
PowerShell/Python jump-box executors) and enterprise systems of record (ServiceNow, CyberArk,
Dynatrace). Automation engineers govern *what can run*; operators compose and execute their own
flows from approved building blocks on a **visual orchestration canvas**.

> North star: **build it once, govern it centrally, let anyone run it safely.**

## Highlights

- **Visual Orchestration Canvas** — drag nodes, bind each to a backend via a connector dropdown
  (Ansible playbooks / Terraform plan-apply / scripts / ServiceNow CMDB / CyberArk / Dynatrace),
  add conditions, approval gates, retries, and run it with live streamed logs.
- **Vendor-agnostic by construction** — every backend is reached through a stable connector port;
  adding one is a new adapter, nothing else changes.
- **Governed self-service** — RBAC (Org → Team → AssetGroup), approval gates, and request
  validation; operators stay inside guardrails engineers define.
- **Alive in simulation** — a stateful simulation layer streams realistic ANSI logs, drives the
  job lifecycle, and seeds a lived-in history, so the whole system is demonstrable without
  connecting real backends.

## Architecture

Domain-Driven Design organized as **vertical slices** (bounded contexts), each owning its full
stack (domain → application → infrastructure → api). See
[`specs/00_foundation/architecture.md`](specs/00_foundation/architecture.md) and the
[Canvas Orchestration spec](specs/02_canvas_orchestration/canvas_orchestration.md).

- **Backend** — Python 3.11+ · FastAPI · SQLAlchemy 2.0 (SQLite/WAL) · synchronous DB
  ([ADR-0004](specs/adr/ADR-0004-synchronous-sqlalchemy.md)).
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

**Demo users** (seeded): `admin` / `engineer` / `operator` / `consumer` — password is the
username + `123` (e.g. `operator123`). Dev-only.

## Testing

```bash
cd backend && .venv/Scripts/python -m pytest && .venv/Scripts/python -m ruff check .
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
```

CI runs all of the above on a self-hosted runner for every PR (`.github/workflows/ci.yml`).

## Status

Pre-1.0/`0.x`. See [`CHANGELOG.md`](CHANGELOG.md) and the delivery
[`roadmap`](specs/00_foundation/roadmap.md). The agent operating manual is
[`CLAUDE.md`](CLAUDE.md); project specifics live in [`.claude/project.md`](.claude/project.md).

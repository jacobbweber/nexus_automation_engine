# Project Profile — Nexus Automation Engine

This file holds **all project-specific facts** referenced by the project-agnostic
operating manual in [`CLAUDE.md`](../CLAUDE.md). When the manual says `$VARIABLE`, the value
lives here. Keep `CLAUDE.md` identical across repos; put anything project-specific here.

---

## 1. What this project is (one paragraph)

**Nexus Automation Engine** is a unified, **vendor- and platform-agnostic Automation Control
Plane**. It puts a single, simple, secure front end over messy, dispersed backend automation
systems (Ansible AAP, Terraform, PowerShell/Python jump-box executors) and enterprise systems
of record (ServiceNow CMDB/Request, CyberArk, Dynatrace). Automation engineers retain strict
control and approval over *what can run*; front-line operators compose and execute their own
flows from approved building blocks through a **visual orchestration canvas**. The product's
reason for existing is to make the nuance and difficulty of operating heterogeneous backend
systems disappear behind one coherent, powerful-but-simple experience.

The north star: **"build it once, govern it centrally, let anyone run it safely."**

---

## 2. Profile Variables (the `$VARIABLE` table the manual reads)

| Variable | Value |
| --- | --- |
| `$SPEC_DIR` | `specs/` |
| `$ADR_DIR` | `specs/adr/` |
| `$GLOSSARY` | `specs/00_foundation/glossary.md` |
| `$SRC_DIR` | `backend/app/` (Python) and `frontend/src/` (TypeScript/React) — see §4 |
| `$TEST_DIR` | `backend/tests/` (pytest) and `frontend/src/**/__tests__/` (vitest) |
| `$STACK` | Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) backend · React 18 + Vite + TypeScript + Tailwind frontend · Docker (multi-stage, rootless, OpenShift-SCC-safe) |
| `$TEST_CMD` | `pytest` (backend, from `backend/`) and `npm run test` (frontend, from `frontend/`) |
| `$LINT_CMD` | `ruff check . && ruff format --check .` (backend) and `npm run lint && npm run typecheck` (frontend) |
| `$RUNNER_LABELS` | `[self-hosted, nexus]` |
| `$VERSION_LINE` | `0.x` (pre-MVP; breaking changes permitted within MINOR) |
| `$ONE_POINT_OH` | See §3 below |

> Tooling note: the CI workflow ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml))
> currently runs the runner smoke test plus **stubbed** lint/test stages. As the backend and
> frontend land, wire `$LINT_CMD` and `$TEST_CMD` into those stages (replace the stubs).

---

## 3. `$ONE_POINT_OH` — the concrete 1.0 / MVP definition

Nexus is **1.0** when a non-developer operator can, in one session and without touching a
backend system directly:

1. **Authenticate** and be scoped by RBAC (Organization → Team → AssetGroup) so they only see
   and run what they are entitled to.
2. **Browse the unified catalog** of approved automation building blocks spanning *all* engines
   (Ansible, Terraform, native script) behind one consistent card/survey UI.
3. **Compose a flow on the visual Canvas** — drag nodes, bind each node to a concrete backend
   (e.g. "this node runs *these* Ansible playbooks", "this node looks up inventory in
   ServiceNow CMDB", "branch on a condition", "require human approval", "then Terraform apply")
   — and save it as a governed, versioned workflow.
4. **Execute it** with live, streamed, ANSI-rendered logs; human-approval gates that actually
   pause and resume; per-node retry/error branches; and a correlated telemetry pane.
5. **Trust the guardrails**: engineers' approval/ownership of building blocks is enforced;
   secrets are leased at runtime (CyberArk) and never persisted; production runs validate an
   approved ServiceNow request; every run is fully audited and replayable.
6. The whole thing **runs containerized** locally (Docker Compose) and is deployable to
   OpenShift, with a stateful simulation backend so the system is demonstrably "alive" end to
   end without requiring the real backends to be connected.

Until all six hold against tests/evals, we are pre-1.0.

---

## 4. Source layout — DDD Vertical Slices (the shape of the code)

Nexus is organized by **bounded context as a vertical slice**, not by technical layer. Each
context owns its full stack (domain → application → infrastructure → api) and is independently
testable. See [`specs/00_foundation/architecture.md`](../specs/00_foundation/architecture.md)
for the full rationale and rules; this is the at-a-glance map.

```text
backend/app/
├── platform/                 # composition root: FastAPI app, async DB, config, security middleware
├── shared_kernel/            # cross-context primitives ONLY (value objects, ids, errors, VariablePool)
└── contexts/                 # one folder per bounded context = one vertical slice
    ├── identity_access/      # Users, Orgs, Teams, RBAC entitlement evaluation
    ├── automation_catalog/   # Unified runner templates, survey schemas, ownership/approval
    ├── orchestration_canvas/ # ★ the visual DAG/canvas engine (see canvas_orchestration.md)
    ├── execution_engine/     # Job lifecycle state machine, log streaming, run telemetry
    ├── connectors/           # Backend adapters: ansible, terraform, script, servicenow, cyberark, dynatrace
    └── observability/        # Audit trail, run history, metrics aggregation
        each context = { domain/  application/  infrastructure/  api/  tests/ }

frontend/src/
├── app/                      # shell: routing, providers, auth context, theme
├── shared/                   # design system, primitives, hooks, api client
└── features/                 # one folder per slice, mirroring backend contexts
    ├── catalog/  ├── canvas/  ├── console/  ├── admin/  └── auth/
```

**Rule:** contexts talk to each other only through published application-layer contracts or
the shared kernel — never by reaching into another context's domain/infrastructure internals.

---

## 5. Key constraints & non-negotiables (project-specific)

- **Vendor/platform agnostic by construction.** No backend vendor's vocabulary leaks into the
  domain or the operator UI. New backends arrive as **connectors** behind a stable port; adding
  one must not modify the canvas, catalog, or execution-engine contexts.
- **Two audiences, one product.** Engineers/admins get deep, highly-extensible governance
  (ownership, approval, RBAC, connector config). Operators get a simple, guided surface. Never
  sacrifice a critical capability to achieve simplicity — hide complexity, don't remove it.
- **The Canvas is the centerpiece**, ported in full from the Ava-POC Foundry and re-aimed at
  backend orchestration. Not a single capability of that feature may be dropped — see the spec.
- **Security posture:** runtime secret leasing (CyberArk), no secrets in DB/logs, production
  runs gated on approved ServiceNow requests, full audit trail, rootless containers.
- **Stateful realism:** the POC backend is a real state machine over SQLite (WAL), not static
  mocks — streaming logs, lifecycle transitions, seeded history.

---

## 6. Source-of-inspiration provenance

The visual orchestration canvas is **ported and adapted** from the sibling proof-of-concept at
`Ava-POC` (the "DAG Pipeline Foundry", a Dify-class canvas builder). We harvest the *entire*
DAG/canvas subsystem — engine, node model, VariablePool, parallel execution, human-in-the-loop
approvals, run/version history — and re-target every node toward backend automation. The Ava
LangGraph runtime and Ava's agent/LLM-centric framing are **reference only**; Nexus is an
infrastructure orchestration product, not an LLM agent shell. See ADR-0002.

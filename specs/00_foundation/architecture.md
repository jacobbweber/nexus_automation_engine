# Architecture — Nexus Automation Engine

**Status:** Foundation spec · **Approach:** Domain-Driven Design organized as Vertical Slices
· See [ADR-0001](../adr/ADR-0001-ddd-vertical-slice-architecture.md).

This is the ground-truth map of how Nexus is structured and *why*. It governs every context
spec. Read [`_conventions.md`](./_conventions.md) and [`glossary.md`](./glossary.md) alongside it.

---

## 1. The core problem we are modeling

Backend automation in an enterprise is **dispersed and heterogeneous**: Ansible controllers,
Terraform state, jump-box scripts, plus systems of record (ServiceNow), secret vaults
(CyberArk), and observability (Dynatrace). Each speaks its own protocol, has its own auth, its
own failure modes. Today an operator must understand all of them to get anything done; an
engineer must hand-hold every run to keep it safe.

Nexus's job is to **collapse that dispersion into one governed, composable surface** without
lying about the underlying reality. The domain is therefore *orchestration and governance of
heterogeneous execution*, not any one vendor's feature set. DDD is the right lens because the
hard part is the **model and its boundaries**, not the plumbing.

## 2. Why DDD + Vertical Slices (not layers-by-technology)

A traditional layout groups by technical role (`models/`, `services/`, `api/`). That spreads a
single capability across the whole tree and couples unrelated features through shared layers —
exactly the wrong shape for a product whose entire value proposition is **isolating change**
(add a connector, add a node type) behind stable seams.

Instead we use **bounded contexts, each implemented as a vertical slice**:

- A **bounded context** is a part of the domain with its own consistent language and model
  (Identity & Access ≠ Orchestration Canvas ≠ Execution). Terms mean one thing inside a context.
- A **vertical slice** means each context owns its *entire* stack — domain, application,
  infrastructure, api, tests — in one folder. You can reason about, test, and change a feature
  without spelunking five technical layers.
- **Layers live *inside* a slice**, smallest-dependency-inward (Hexagonal / Ports & Adapters):

  ```
  api ──▶ application ──▶ domain ◀── infrastructure
         (use cases)     (pure rules)   (adapters: db, http, vendors)
  ```

  The **domain** is pure and vendor-free. **Application** orchestrates use cases (commands &
  queries). **Infrastructure** implements ports (DB repos, vendor clients). **Api** exposes
  REST/WebSocket. Dependencies always point *toward* the domain.

## 3. The bounded contexts (the slices)

| Context | Responsibility (its "Why") | Ubiquitous language it owns |
| --- | --- | --- |
| **identity_access** | Who you are, what you may touch. RBAC entitlement evaluation down Org→Team→AssetGroup. | User, Organization, Team, AssetGroup, ResourcePermission, Role, Entitlement |
| **automation_catalog** | The library of *approved building blocks* operators can use; their ownership, survey schemas, and approval state. | Template, Survey, BuildingBlock, Owner, ApprovalState, Capability |
| **orchestration_canvas** ★ | The visual DAG/canvas: compose nodes into governed, versioned flows. The product centerpiece. | Workflow, Node, Edge, Port, VariablePool, Run, Step, Approval, Version |
| **execution_engine** | The job lifecycle state machine: PENDING→RUNNING→SUCCESS/FAILED/CANCELLED, log streaming, run telemetry. | Job, Run, LogStream, Lifecycle, CheckMode, DiffMode, Telemetry |
| **connectors** | Vendor-agnostic ports + concrete adapters to each backend/system of record. | Connector, Adapter, Port, Inventory, Credential lease, Request validation |
| **observability** | Audit trail, run history, correlation of execution with platform events. | AuditEvent, RunHistory, Metric, Correlation |

`shared_kernel` holds only what is genuinely cross-context and stable: identifiers, base value
objects, error types, and the **`VariablePool`** primitive (used by the canvas to resolve typed,
dot-notation references and expressions — see canvas spec). Nothing vendor-specific ever lives
in the shared kernel.

## 4. Context relationships (context map)

```text
                  identity_access  (entitlement checks, upstream of everything)
                         │
        ┌────────────────┼─────────────────────────┐
        ▼                ▼                          ▼
 automation_catalog   orchestration_canvas ─────▶ execution_engine
   (building blocks)   (compose + govern flows)     (run lifecycle, streams)
        │                     │                          │
        └─────────────────────┴───────────┬──────────────┘
                                           ▼
                                      connectors  (ansible│terraform│script│
                                                   servicenow│cyberark│dynatrace)
                                           │
                                           ▼
                                     observability (audit, history, telemetry)
```

- **Relationship types:** `orchestration_canvas` is a *customer* of `connectors` and
  `execution_engine` (downstream, conformist to their published contracts). `identity_access` is
  an *upstream* guardian — every command passes an entitlement check. `connectors` is an
  **Anti-Corruption Layer**: vendor models are translated into Nexus's language at this seam and
  never leak inward.
- **Integration rule:** contexts communicate only via published **application contracts**
  (commands/queries/DTOs) or the shared kernel. Reaching into another context's `domain/` or
  `infrastructure/` is forbidden and will be flagged in review.

## 5. The Connector Port — how "vendor/platform agnostic" is enforced

Every backend is reached through one stable port (illustrative):

```python
class ExecutionConnector(Protocol):
    capabilities: ConnectorCapabilities          # supports_check_mode, supports_diff, streams?
    async def discover(self, query: DiscoveryQuery) -> list[Resource]   # e.g. CMDB inventory
    async def dispatch(self, request: ExecutionRequest) -> RunHandle    # start work
    async def stream(self, handle: RunHandle) -> AsyncIterator[LogEvent]
    async def status(self, handle: RunHandle) -> RunStatus
    async def cancel(self, handle: RunHandle) -> None
```

Adding Ansible, Terraform, a script executor, or a future vendor means writing one adapter that
satisfies this port. **No other context changes.** Systems-of-record (ServiceNow CMDB, CyberArk,
Dynatrace) implement narrower ports (`DiscoveryPort`, `SecretLeasePort`, `ApprovalPort`,
`TelemetryPort`). This is the seam that makes the canvas able to say "this node = Ansible / this
node = a CMDB lookup" generically.

## 6. Front-end architecture & design philosophy

The UI mirrors the backend slices as **feature folders** (`features/catalog`, `features/canvas`,
`features/console`, `features/admin`, `features/auth`) over a shared design system. Strict
separation of presentation components from state/api hooks (per blueprint).

**Design philosophy — "simple surface, deep spine":**

1. **Two altitudes, one product.** Operators see a guided, low-friction surface (catalog cards,
   guided surveys, a canvas that snaps together approved blocks, a clean run console). Engineers
   and admins get a deep, **highly extensible** management plane (connector config, ownership &
   approval of building blocks, RBAC matrices, node-type governance). The same domain powers
   both; we *hide* complexity behind progressive disclosure, we never *remove* capability to
   look simple.
2. **The canvas makes dispersion feel unified.** The nuance of orchestrating Terraform → Ansible
   → CMDB lookup → approval → script is expressed as a few connected nodes. The difficulty is
   real and lives in the connectors/engine; the operator experiences it as a clean flow.
3. **Honest, live feedback.** Streaming ANSI logs, real lifecycle state, correlated telemetry,
   approval gates that actually block — the UI never fakes "done." State changes reflect without
   refresh (WebSocket).
4. **Governed self-service.** Operators build and run their *own* flows, but only from blocks
   engineers approved, scoped by RBAC, with production runs gated on approved requests. Freedom
   inside guardrails.
5. **Visual identity.** High-contrast neutral slate/charcoal dark-and-light theme suited to long
   operations monitoring; accessible primitives (Radix), Lucide iconography, Tailwind tokens.

## 7. Cross-cutting platform concerns

- **Async-first** Python (FastAPI/Uvicorn), `asyncio` background workers for run execution and
  log streaming.
- **State:** SQLAlchemy 2.0 over SQLite in **WAL mode** (concurrent UI reads + worker writes);
  one DB-connection helper, no scattered `sqlite3.connect`. Read-mostly UI / read-write runner
  separation by convention (harvested lesson from Ava-POC).
- **Security middleware** (JWT, RBAC enforcement) is platform-level, applied before any context
  command runs. Secrets are leased at runtime and never persisted (CyberArk port).
- **Containerization:** multi-stage, rootless, OpenShift-SCC-safe.

## 8. Testing strategy (maps to the CI pyramid in `CLAUDE.md §8`)

- **Domain unit tests** per slice (pure, fast, no I/O).
- **Application/use-case tests** with in-memory port fakes.
- **Connector contract tests**: every adapter is verified against the port's contract (including
  the simulation adapter), so the canvas can trust any connector.
- **Integration tests** across slices (api → application → infra with a temp DB).
- **Behavioral evals** for the realistic simulation engine (streams, lifecycle, seeded history).
- **Container/QA smoke**: build the image, run it, exercise a real flow.

## 9. Open questions

- Multi-tenant isolation depth at 1.0 (single-org demo vs. full Org partitioning of state).
- Whether `connectors` should be one context or split per integration as it grows.
- LangGraph durable runtime: harvest later or keep canvas-DAG-only for 1.0 (ADR-0002 leans
  canvas-only first).

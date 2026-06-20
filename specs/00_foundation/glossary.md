# Glossary — Nexus Automation Engine

The single source of truth for Nexus vocabulary (`$GLOSSARY`). Per `CLAUDE.md §9`, terminology
drift is corrected against this file. Abstract concepts carry a **mental model** (what it is
*and how it flows*), not just a one-line definition.

---

## Product-level

**Automation Control Plane** — *what Nexus is.* A governing layer that sits above many backend
automation systems and presents one secure, composable surface. Mental model: think of an
air-traffic control tower. The planes (Ansible, Terraform, scripts) still fly themselves; the
tower gives unified visibility, sequencing, clearance (approval), and a single place to direct
traffic — without flying any plane itself.

**Vendor/platform agnostic** — no backend's vocabulary or assumptions leak into the domain or
operator UI. A new backend is added as a *connector* behind a stable port; nothing else changes.

**Building block** — an approved, reusable unit an operator may place into a flow (an Ansible
template, a Terraform config, a CMDB lookup, a script). Owned and approved by engineers; surfaced
in the catalog; bound to a canvas node.

## DDD structural terms

**Bounded context** — a region of the domain with its own consistent language and model. A term
means exactly one thing inside a context. Nexus contexts: identity_access, automation_catalog,
orchestration_canvas, execution_engine, connectors, observability.

**Vertical slice** — a feature/context implemented top-to-bottom in one folder (domain →
application → infrastructure → api → tests), so it can be understood and changed in isolation.
Contrast with horizontal layering (grouping all models together, all services together).

**Layer (within a slice)** — *domain* (pure rules, no I/O), *application* (use cases =
commands/queries), *infrastructure* (adapters: DB, HTTP, vendor clients), *api* (REST/WS).
Dependencies point inward toward the domain.

**Shared kernel** — the small, stable set of types shared across contexts (ids, value objects,
errors, the VariablePool). Never holds vendor-specific code.

**Anti-Corruption Layer (ACL)** — the translation seam (the `connectors` context) where a
vendor's model is converted into Nexus's language so external concepts never corrupt the domain.

**Port / Adapter** — a *port* is the interface the domain depends on (e.g. `ExecutionConnector`);
an *adapter* is a concrete implementation (AnsibleAdapter, TerraformAdapter, the simulation
adapter). Ports & Adapters = Hexagonal architecture.

## Canvas / orchestration terms

**Canvas (Orchestration Canvas)** — *the centerpiece.* A visual, Dify-class workflow builder
where operators drag **nodes**, connect them with **edges**, and bind each node to a concrete
backend action. Mental model: a wiring diagram that is also executable. You draw the plan
(Terraform apply → wait for approval → run these Ansible playbooks → look up affected CIs in
CMDB), and the same diagram *is* the thing that runs, lighting up node-by-node as it executes.

**Workflow** — a saved, named, versioned graph (nodes + edges + layout). The governed artifact a
flow lives in.

**Node** — one step on the canvas. Has a `type` (the kind of work) and `data` (its parameters).
Each actionable node binds to a backend via a connector selection (e.g. type=`automation_task`,
connector=`ansible`, playbooks=[...]).

**Edge** — a directed connection from a source node's output **port** to a target node's input
port. Edges carry control flow; condition/switch edges carry a `sourceHandle` (`true`/`false`/
`case_x`/`error`) that decides activation.

**Port (canvas)** — a connection point on a node (an output or input handle). Condition nodes
expose `true`/`false`; switch nodes expose one per case; any node can expose an `error` handle.

**VariablePool** — *how data flows between nodes.* A scoped store mapping `node_id` → that node's
output, supporting deep dot-notation (`{{cmdb_lookup.result.items[0].name}}`), safe expression
evaluation (`{{count.value > 5}}`), and Jinja2-lite templating in any text field. Mental model:
a shared whiteboard the running graph reads and writes — each node posts its result, downstream
nodes reference it by name.

**Run** — one execution of a workflow. Has a lifecycle status (running/completed/failed/
cancelled), inputs, outputs, and a set of **steps**.

**Step** — the execution record of a single node within a run (status, inputs, outputs, error,
retry count). Drives the live canvas highlighting and the replayable history.

**Human-in-the-loop / Approval gate** — a node (`human_input`) that *pauses* the run, pushes an
approval request to the UI over WebSocket, and blocks until a user approves/rejects (with
optional text). The core mechanism letting engineers keep "strict control and approval."

**Skipped propagation** — when a condition routes one way, the not-taken branch's nodes are
marked `skipped`, and that status flows downstream so the graph never hangs waiting on a dead
branch (unless a node has another active incoming edge — logical OR).

**Parallel execution** — independent branches run concurrently. A node runs as soon as its
in-degree of unresolved parents hits zero; concurrency is bounded by a semaphore.

## Execution & governance terms

**Job / Execution** — a unit of backend work dispatched through a connector (an Ansible job, a
Terraform run, a script invocation). A canvas `automation_task` node produces a job.

**Lifecycle** — the job/run state machine: PENDING → RUNNING → SUCCESS | FAILED | CANCELLED,
managed by an asyncio background worker; UI reflects transitions without refresh.

**Check mode / Diff mode** — dry-run semantics. Check mode shows what *would* change without
mutating; diff mode shows the before/after. First-class because operators must preview safely.

**RBAC entitlement** — authorization resolved down the chain Organization → Team → AssetGroup →
ResourcePermission. A global role (admin/engineer/operator/consumer) is the baseline; explicit
resource permissions refine it. Evaluated before any command executes.

**Credential lease** — a short-lived secret fetched from CyberArk at execution time, held only
in memory for the run, never persisted to DB or logs.

**Request validation (RITM)** — before a production-affecting run, the engine validates that a
referenced ServiceNow request item is in an approved state. Governance gate, not just metadata.

**Simulation engine** — the stateful backend that makes the POC "alive": real SQLite (WAL) state,
streamed realistic logs with ANSI + jitter, seeded historical runs, and a simulation **connector
adapter** that satisfies the same port as the real ones.

## Connectors (the backends we abstract)

**Ansible (AAP/Controller)** — configuration management; runs playbooks/job templates/workflows.
**Terraform** — infrastructure-as-code; plan/apply with state and drift.
**Script executor** — PowerShell/Python on Windows/Linux jump-boxes via SSH/WinRM.
**ServiceNow** — system of record: CMDB inventory discovery + request (RITM) approval validation.
**CyberArk** — secret vault: runtime credential leasing.
**Dynatrace** — observability: correlate job runs with platform events/metrics.

## Experience & theming (see `specs/05_experience/`)

**Design token** — a named visual value (color, spacing, radius, type, shadow, motion). Tokens are
*primitive* (raw ramps/scales, never used directly) or *semantic*. Shipped as both CSS custom
properties and a generated TS-constants module so canvas/SVG/chart rendering can't drift from CSS.

**Semantic token contract** — the fixed set of semantic keys (`--bg`, `--surface`, `--accent`,
`--run-*`, …) that components are allowed to consume. The contract is the stable interface; every
resolver (mode/area/theme) only ever remaps these keys.

**Resolution cascade** — the ordered CSS `@layer` stack
(`reset → primitives → semantic → mode → area → theme → density → a11y`) that makes every
mode × area × theme × density × accessibility combination valid by construction. Mental model:
one contract, many resolvers stacked by precedence; accessibility always wins on top.

**Area-context override** — a bounded retint applied when a Nexus surface (Dashboard/Catalog/
Canvas/Library/Console/Incidents/Governance/Admin) is active: it may change only accent and tint,
never layout, and never collide with protected status colors.

**Protected status semantics** — `--run-*` and `--success/warn/danger/info` are validated for
mutual distinguishability + colorblind safety and are always paired with an icon/shape in
components. Operational legibility outranks any theme.

**Theme (`nexus-theme/v1`)** — a theme expressed as data: a JSON document that remaps an
allow-listed semantic key set for light+dark, validated server-side before delivery. It can never
contain selectors, layout, spacing scale, or font files.

**Theme Studio** — the fully deterministic pipeline (form + color pickers + live preview +
validator) for authoring themes. There is **no AI/LLM** in it or anywhere in the system (ADR-0008); the deterministic
validator is the sole gate, so a theme is safe by construction.

**Density** — `cozy | comfortable | compact`, a multiplier over the spacing/type scale (clamped so
interactive targets stay ≥44px). Lets the same locked layout serve a relaxed novice view and a
dense expert/enterprise view.

## Deterministic governance (v4.0 — see `vision_deterministic_governance.md`)

**CI Type Schema** — *schema-as-data for the CMDB.* The definition of what a CI of a given type
(VM, Datastore, Cluster, Volume, …) must look like: its fields (name, datatype, required, allowed
values/regex, sensitivity) and required tags/naming patterns. Authored/maintained in the CMDB Schema
Studio, validated deterministically. Mental model: the same idea as `nexus-theme/v1` or `node_specs`,
applied to configuration items — a contract the platform enforces, not free-form records.

**Lineage (CI lineage)** — *what makes a CI whole.* The typed graph of required relationships for a
CI type, with cardinality (a VM resolves `host→cluster→datacenter`, a datastore, a backup policy, an
owner/team, an environment). Lineage is about a CI's *relationships*, distinct from its own fields.

**CI Health Report** — the deterministic output of checking a CI against its type schema **and**
lineage: missing/invalid fields, broken/missing/orphaned relationships, tag/naming non-compliance,
a health score, and remediation hints. The enriched basis for the lifecycle-validation gate.

**Idempotency class** — a building block / connector action's declared re-run safety: `idempotent`
(converges to desired state, safe to re-run), `check_only` (read/plan), or `non_idempotent` (must be
guarded — flagged). The mandate "all automation is idempotent" expressed *in the contract*.

**Compliance mode / DriftReport** — *assert, don't change.* Running a template/workflow in compliance
mode performs a dry-run that yields a **DriftReport** (desired vs observed, per resource & field:
`compliant | drifted | unknown`, plus the reconcile action that would converge it) without mutating.
Mental model: GitOps reconcile applied to the estate — run anything anytime to see the gap.

**Change classification** — deterministic label for a run — `standard` (pre-approved low-risk),
`normal` (needs review/approval), `emergency` (expedited) — derived from building-block risk, blast
radius, targets, and idempotency class. Policy maps classification → required reviewer levels.

**Plain summary** — authored, human-language metadata on a building block: `input → action →
outcome` slots. Composed in execution order (with resolved variables) to generate review narratives.
Authored once by the automation team; every workflow built from the block inherits exec-ready prose.

**Change Review Packet** — the deterministic, multi-representation rendering of exactly what a run
will do: **Technical** (graph, params, plan/diff, blast radius), **Non-technical/Executive** (plain
narrative from plain summaries), and **Flowchart** (human-labelled `LogicFlow`). An audience toggle
(Technical / Non-technical / Executive) switches the view. No AI — composed from authored templates.

**Pinning Rule** — *a guaranteed binding of a workflow to matching CIs.* `selector (CI type + tags +
fields) → guaranteed workflow + trigger (create/change/schedule/on-demand) + enforcement mode
(assert | enforce | gate) + priority`. Mental model: management-by-invariant — admins declare what
must be true of the estate ("every DR-Tier-0 VM has a Zerto VPG"); the reconciler continuously
asserts it, enforces through review, and surfaces coverage and gaps.

**Reconciler (pinning)** — the engine that, per trigger, evaluates pinning rules against CMDB CIs and
produces a pinned-actions plan: `assert` launches compliance runs, `enforce` routes review-gated
reconcile runs, `gate` blocks the triggering change until the pinned check passes.

**GitOps backbone / config-as-code** — Nexus serializes all config artifacts (workflows, CI schemas,
pinning rules, themes, policies, change templates, schedules) to a **canonical, deterministic** Git
layout, commits on change (audit message) and on schedule as backup/system-of-record, and can
optionally **pull/reconcile** a repo as desired state. Default repo is local (guardrail: official git,
no paid/remote services). Enables per-artifact history/diff/restore and environment promotion.

**infracode pillar repos** — the org/repo strategy for the *automation content* (separate from the
Nexus platform-config repo): one mono/pillar repo per integration — `infracode_ansible`,
`infracode_terraform`, `infracode_snow`, `infracode_pure`, `infracode_cisco`. Nexus references/syncs
them; deterministic naming/tagging conventions live here. Documented, not a runtime dependency.

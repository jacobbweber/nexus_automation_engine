# Canvas Orchestration Spec — Nexus Automation Engine

- **Bounded context:** `orchestration_canvas` (the product centerpiece)
- **Ported from:** Ava-POC "DAG Pipeline Foundry" (a Dify-class visual workflow builder),
  re-targeted from LLM agent orchestration to **backend automation orchestration**. See
  [ADR-0002](../adr/ADR-0002-port-foundry-canvas-as-orchestration-core.md).
- **Status:** Foundation spec (v1). **Mandate:** *no capability of the source feature may be
  dropped.* This document is the checklist that proves completeness.

---

## 🎯 Goal

A **visual workflow canvas** where an operator drags nodes onto a pan/zoom canvas, wires them
with edges, and **binds each actionable node to a concrete backend** via a dropdown — "this node
runs *these* Ansible playbooks", "this node does a ServiceNow CMDB lookup", "branch on this
condition", "require human approval", "then Terraform apply", "then run a script". The same
diagram **is** the executable: it lights up node-by-node as it runs, streaming live logs.

This is how Nexus turns the nuance of orchestrating dispersed backends (Terraform infra →
Ansible post-config → CMDB lookups → approvals → scripts) into a single, simple, governed flow.
Automation engineers govern the building blocks and approvals; operators compose and run their
own flows from them.

## 💡 Use cases & value

- **Bridge Terraform → Ansible seamlessly.** Provision infrastructure, then hand off to
  post-configuration playbooks, with CMDB enrichment and approval gates in between — one canvas,
  no context-switching across tools.
- **Governed self-service.** Operators build flows only from engineer-approved building blocks,
  scoped by RBAC; engineers keep strict control via approval gates and node-type governance.
- **Human-in-the-loop on high-risk steps.** Pause before a production apply/mutation; notify
  over WebSocket; resume on approval (with optional text).
- **Fail-safe processing.** Per-node retries, timeouts, and dedicated **error branches** so one
  failure doesn't abort the whole flow.
- **Reusability & versioning.** Save flows, snapshot versions, replay run history, compose
  sub-workflows.
- **(Future) Autonomous assembly.** The system can draft a canvas from an intent and present it
  for approval (mirrors Ava's self-build loop; reference, not 1.0-blocking).

---

## 🧱 Design pillars (ported in full from the source, all required)

### 1. Typed VariablePool (data flow between nodes)
A scoped store mapping `node_id → output`. Capabilities (all required):
- **Deep dot-notation:** `{{cmdb_lookup.result.items[0].name}}`.
- **Safe expression evaluation:** `{{counter.value + 1}}`, `{{count.value > 5}}` — evaluated
  against the nested pool with a restricted builtins set (`len,str,int,float,list,dict,bool,
  range`), never arbitrary code.
- **Jinja2-lite templating** in any text field (loops/conditionals inside prompts, bodies,
  templates).
- **Exact-replacement fast path** for a lone `{{ref}}` returns the *typed* value (not a string).
- Implemented as a `shared_kernel` primitive so every context can resolve references uniformly.

### 2. Parallel graph execution engine
- Compile to a directed graph; **topological sort**; **abort on cycle** (must be a DAG).
- A node runs as soon as **all incoming parents are resolved** (in-degree of unresolved parents
  hits 0) — independent branches run **concurrently** via `asyncio.gather` bounded by a
  **semaphore** (default 5).
- **Skipped-path propagation:** when a condition/switch routes one way, edges not matching the
  result are marked `skipped`; target nodes go `skipped` unless they have another *active*
  incoming edge (logical OR); skip propagates downstream so the graph never hangs.

### 3. Per-node resilience
- `max_retries`, `retry_delay_seconds`, `timeout_seconds` per node.
- **Error edge** (`sourceHandle: "error"`): on terminal failure, if an error branch exists the
  node yields `{"error": ...}` and flow continues down that branch; otherwise the run fails.

### 4. Execution history & step logging (persistent + live)
- Every run and every step persisted to SQLite (see schema). Step states: `pending`, `running`,
  `completed`, `failed`, `skipped` with inputs/outputs/error/retry_count.
- **Real-time WebSocket stream** of run + step transitions to the canvas (live node highlight)
  and the run terminal.
- **Run history** replayable; **version snapshots** of the graph; **prune** old runs (keep N).

### 5. Human-in-the-loop interrupts
- A node can **pause** the run, register a pending approval future keyed by `run_id/node_id`,
  push `workflow_approval_required` over WS, and **block** (with timeout) until a resume call
  resolves it. Rejection fails the node (which may route to an error branch).

---

## 🧩 Node catalogue

Every node JSON follows `{ id, type, position:{x,y}, data:{...} }`. `data.name` is the display
label. Resilience fields (`max_retries`, `retry_delay_seconds`, `timeout_seconds`) are valid on
any actionable node.

### A. Generic flow nodes (ported verbatim from the Foundry — all 15 retained)

| Type | Purpose | Key `data` fields |
| --- | --- | --- |
| `start` | Declares workflow input variables. | `inputs: [{name,type,default}]` |
| `end` | Terminates, compiles return values. | `outputs: {key: "{{ref}}"}` |
| `code` | Sandboxed Python (`def main(inputs)->dict`) in an isolated process. | `code`, `inputs` |
| `condition` | Boolean test → `true`/`false` ports. | `variable`, `operator` (`==`,`!=`,`>`,`<`,`contains`,`is_empty`), `value` |
| `switch_router` | Multi-way routing by value match. | `variable`, `cases:[{value,target_handle}]`, `default_handle` |
| `http_request` | REST call (GET/POST/PUT/DELETE). | `method`, `url`, `headers`, `body` |
| `template_transform` | Render a Jinja2 template. | `template`, `variables` |
| `iterator` | Run a **sub-graph** per item of an array, collect outputs. | `items_variable`, `sub_graph:{nodes,edges}` |
| `human_input` | Pause for approval/text; blocks until resumed. | `message`, `require_text_response`, `timeout_seconds` |
| `delay` | Pause N seconds. | `delay_seconds` |
| `variable_assigner` | Write/accumulate values into the VariablePool. | `assignments:[{key,value}]` |
| `sub_workflow` | Run another saved workflow inline. | `workflow_id`, `inputs` |
| `tool` | Invoke a registered system tool/plugin. | `tool_name`, `args` |
| `knowledge_retrieval` | Hybrid keyword+vector retrieval (docs/runbooks). | `query`, `limit` |
| `llm` | LLM call (retained for summarization/decision aids; **optional**, not core to infra). | `model`, `system_prompt`, `prompt`, `temperature`, `max_tokens` |

> The `llm`, `tool`, and `knowledge_retrieval` nodes are preserved from the source so no
> capability is lost, but in Nexus they are *supporting* nodes — useful for summarizing a run,
> enriching a decision, or pulling a runbook — not the centerpiece. The infra nodes below are.

### B. Backend-integration nodes (the Nexus re-targeting — the heart of the request)

These give each actionable node a **connector dropdown**. Selecting a connector reveals that
connector's parameter form (discovered from its capabilities), so the canvas is generic but the
node renders the right fields for Ansible vs Terraform vs script vs CMDB.

| Type | Purpose | Key `data` fields |
| --- | --- | --- |
| `automation_task` ★ | The universal backend-action node. Pick a **connector** then its action. | `connector` (`ansible`\|`terraform`\|`script`\|…), `action`, connector-specific params (below), `check_mode`, `diff_mode`, `asset_group_id` |
| `cmdb_lookup` | ServiceNow CMDB inventory discovery → array into the pool. | `connector:"servicenow"`, `table` (e.g. `cmdb_ci_server`), `query`, `fields`, `limit` |
| `request_validation` | Gate on an approved ServiceNow request (RITM). | `connector:"servicenow"`, `ritm` (e.g. `{{start.ritm}}`), `required_state` |
| `secret_lease` | Lease a short-lived credential from the vault (memory-only). | `connector:"cyberark"`, `safe`, `object`, `bind_as` (pool key) |
| `telemetry_probe` | Pull correlated platform events/metrics for context. | `connector:"dynatrace"`, `entity`, `window` |
| `approval_gate` | Governance-flavored `human_input`: typed approval tied to RBAC roles. | `message`, `approver_roles:["engineer","admin"]`, `require_text_response`, `timeout_seconds` |

**`automation_task` connector parameter shapes** (the "dropdown then these playbooks" flow):

```jsonc
// connector = "ansible"
{ "connector": "ansible", "action": "run_job_template",
  "playbooks": ["site.yml", "hardening.yml"],     // or "job_template_id"
  "inventory": "{{cmdb_lookup.result}}",          // bind CMDB output as inventory
  "extra_vars": { "tier": "{{start.tier}}" },
  "check_mode": true, "diff_mode": true }

// connector = "terraform"
{ "connector": "terraform", "action": "apply",     // "plan" | "apply" | "destroy"
  "workspace": "prod-east", "var_file": "prod.tfvars",
  "auto_approve": false }                           // false => pair with an approval_gate

// connector = "script"
{ "connector": "script", "action": "run",
  "shell": "powershell",                            // "powershell" | "bash"
  "target": "{{cmdb_lookup.result.items[0].fqdn}}",
  "transport": "winrm",                             // "winrm" | "ssh"
  "script": "Restart-Service W3SVC" }
```

The canonical end-to-end pattern the user described — *Terraform infra → Ansible post-config,
governed*:

```
start → automation_task(terraform: plan) → approval_gate(engineer) →
automation_task(terraform: apply) → cmdb_lookup(servicenow) →
secret_lease(cyberark) → automation_task(ansible: run playbooks, inventory={{cmdb_lookup.result}}) →
condition(result ok?) ──true──▶ telemetry_probe(dynatrace) → end
                       └─false─▶ automation_task(ansible: rollback) → end
```

All actionable nodes resolve their params through the VariablePool, run via the
`connectors` context ports (so a node never knows it's talking to a real vs simulated backend),
and stream their logs into the same step/run telemetry as every other node.

---

## 🗄️ Persistence (context-owned tables, SQLite WAL)

Ported from the source, kept verbatim in shape:

- **`workflows`** — `id, name, description, graph_json (nodes/edges/zoom/pan), created_at, updated_at`.
- **`workflow_versions`** — `version_id, workflow_id, graph_json, created_at, description`
  (snapshot + revert support).
- **`workflow_runs`** — `run_id, workflow_id, status (running|completed|failed|cancelled),
  started_at, completed_at, inputs_json, outputs_json, error_message`.
- **`workflow_run_steps`** — `step_id, run_id, node_id, node_type, status, started_at,
  completed_at, inputs_json, outputs_json, error_message, retry_count`.

`prune_old_runs(workflow_id, keep=50)`; FK cascades delete steps with runs. All access goes
through the one WAL-mode DB helper (`architecture.md §7`).

> The source also defined LangGraph durable-runtime tables. Nexus defers the LangGraph runtime
> (ADR-0002) — DAG-canvas first. The schema slot is reserved for a future durable executor.

---

## 🔌 Application & API contracts

REST (under `/api/v1/canvas`, RBAC-guarded by `identity_access`):

| Method & path | Purpose |
| --- | --- |
| `GET /workflows` | List workflows (scoped to entitlements). |
| `GET /workflows/{id}` | Get one (graph_json hydrated). |
| `POST /workflows` | Create/replace (`id,name,description,graph_json`). |
| `DELETE /workflows/{id}` | Delete. |
| `POST /workflows/{id}/run` | Start a run; returns `run_id`; streams over WS. |
| `GET /workflows/{id}/runs` | Run history. |
| `GET /workflows/{id}/runs/{run_id}` | Run + its steps (replay). |
| `GET /workflows/{id}/versions` · `POST .../versions` · `POST .../revert/{version_id}` | Version snapshots & revert. |
| `POST /workflows/approval` | Resolve a pending human/approval gate (`run_id,node_id,approved,response`). |

WebSocket frames (server→client), ported set: `workflow_run_start`, `workflow_log`
(`{node_id,node_name,status,outputs?|error?}`), `workflow_approval_required`
(`{run_id,node_id,message,require_text_response}`), `workflow_run_complete`,
`workflow_run_failed`. Client→server resume: `{approved, response}`.

---

## 🖥️ Canvas UI behavior (ported in full)

The source is a **hand-built React pan/zoom canvas** (not react-flow) — re-implement equivalently
in `frontend/src/features/canvas`:

- **Pan & zoom** (wheel-zoom 0.2–3.0, drag-to-pan), grid background scaled to zoom.
- **Node palette** side drawer, grouped categories (Core · Control Flow · Data/RAG · IO/State ·
  **Backend Integrations**), click/drag to add a node at cursor.
- **Draggable nodes** with reposition; **port-based connections** drawn as edges; an edge from a
  port to a port (one incoming edge per target handle replaces a prior one).
- **Colored edges by handle**: `true` (green), `false`/`error` (red), default (neutral).
- **Condition/switch nodes** render multiple output handles (true/false; one per case + default).
- **Properties panel** to edit the selected node's `data` (and, for `automation_task`, the
  **connector dropdown** that swaps the parameter form).
- **Run controls**: run-inputs modal (from `start.inputs`), live per-node state highlighting
  (pending/running/completed/failed/skipped), an **execution terminal** with **ANSI rendering**.
- **Human-approval overlay**: surfaces the gate message, accepts approve/reject + optional text,
  posts the resume.
- **History panel**: list past runs, open a run to replay step states.
- **Save / version / revert** controls.

Visual identity per `architecture.md §6` (high-contrast slate, Radix primitives, Lucide icons,
Tailwind tokens).

---

## ✅ Acceptance criteria (the "didn't miss a piece" checklist)

1. All 15 source node types implemented **and** the 6 Nexus backend-integration node types.
2. VariablePool: dot-notation, safe expressions, Jinja2-lite, typed exact-replacement.
3. Parallel execution with semaphore; cycle detection; skipped-path propagation.
4. Per-node retries/timeouts; error edges continue the flow.
5. Human/approval gates pause→notify→block→resume over WebSocket, with timeout & rejection.
6. Run/step persistence + live WS streaming + history replay + version snapshot/revert + prune.
7. `automation_task` connector dropdown renders connector-specific params and runs through the
   `connectors` ports (Ansible/Terraform/script + CMDB/CyberArk/Dynatrace), real or simulated.
8. The Terraform→approval→Terraform→CMDB→secret→Ansible→branch pattern runs end-to-end against
   the simulation engine with streamed ANSI logs and correct node highlighting.
9. Canvas UI: pan/zoom, palette, drag, port-connect, colored handles, properties panel,
   approval overlay, run terminal, history — all functional (Zero-Placeholder rule).

## ❓ Open questions
- Sub-graph isolation depth for `iterator` (shared vs copied VariablePool — source copies).
- Whether `approval_gate` approver-role enforcement is checked at resume time only or also gates
  who *sees* the pending approval (lean: both, via `identity_access`).
- Connector parameter forms: hand-authored per connector vs. generated from a capability schema
  (lean: capability-schema-driven so new connectors self-describe their node form).

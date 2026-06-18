# ADR-0002 — Port the Ava-POC Foundry canvas as the orchestration core

**Status:** Accepted (2026-06-18)

## Context
A central requirement is a Dify-class visual pipeline/canvas builder, and a complete, working
implementation already exists in the sibling proof-of-concept `Ava-POC` (the "DAG Pipeline
Foundry"): a typed VariablePool, parallel DAG execution with skip propagation, 15 node types,
per-node retries/error edges, human-in-the-loop interrupts, run/step persistence with live
WebSocket streaming, version snapshots, and a hand-built pan/zoom React canvas. The directive:
incorporate this feature **completely**, missing nothing, but re-aimed at orchestrating backend
systems (Ansible, Terraform, scripts, ServiceNow CMDB, CyberArk, Dynatrace) rather than LLM
agents. The Foundry also ships a second, code-first **LangGraph durable runtime**.

## Decision
**Harvest the entire DAG-canvas subsystem** into the `orchestration_canvas` bounded context,
preserving every capability (engine, node model, VariablePool, parallel execution, approvals,
history, versioning, canvas UX) — documented as a completeness checklist in
[`canvas_orchestration.md`](../02_canvas_orchestration/canvas_orchestration.md). **Re-target it**
by (a) keeping the generic flow nodes and (b) adding backend-integration node types whose
**connector dropdown** binds a node to a concrete backend, executed through the `connectors`
context ports so a node is agnostic to real-vs-simulated backends.

**Defer the LangGraph durable runtime.** Ship DAG-canvas first; reserve the schema/seam for a
durable executor later. Treat Ava's LLM/agent framing as **reference only** — Nexus is an
infrastructure orchestration product; `llm`/`tool`/`knowledge_retrieval` nodes are retained as
*supporting* nodes so nothing is lost, but they are not the centerpiece.

## Consequences
**Good:** proven design and execution semantics adopted wholesale (de-risked); the
"dropdown→this backend→these playbooks→conditionals→next" experience the operator wants falls out
naturally; agnosticism is preserved by routing every node through connector ports; full feature
parity is auditable via the checklist.
**Bad / costs:** the source is Python+a bespoke React canvas tightly coupled to Ava's modules
(`llm_router`, `plugin_manager`, profiles) — porting requires re-homing those dependencies onto
Nexus's `connectors`/`platform`; deferring LangGraph means durable, resumable-across-restart
graphs wait; re-implementing the hand-built canvas (vs adopting a library) is real frontend work.

## Alternatives considered
- **Adopt react-flow / a library instead of porting the bespoke canvas:** still open as an
  implementation choice for the UI, but the *engine, node model, and contracts* are ported
  regardless; deferred to the canvas build, not this ADR.
- **Build a fresh canvas from scratch:** rejected — discards a complete, working feature against
  the explicit "don't miss a piece" mandate.
- **Port LangGraph runtime now too:** rejected for 1.0 scope — adds a second execution paradigm
  before the first delivers value.

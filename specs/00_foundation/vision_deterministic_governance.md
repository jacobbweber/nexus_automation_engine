# Vision — Deterministic Governance (v4.0 line)

The 1.0/2.0/3.0 lines built the engine, the management layer, and the operator experience. The
**4.0 line** makes Nexus an **absolute configuration-management control plane**: the CMDB becomes a
*schema-enforced contract*, every change (a CI edit or a workflow run) passes *audience-tailored*
human review, configuration lives in *Git*, deterministic *policy pins* guarantee desired state,
and **all automation is idempotent and continuously re-runnable for compliance**.

This document is the brainstormed plan. It deliberately takes each seed idea *further* — the test
for every feature is **"does this add guaranteed capability, or just complexity?"** Each pillar
below states the seed, the expansion, the *value thesis*, and the bounded-context placement. The
delivery breakdown (milestones M24–M30 → GitHub epics/stories) follows in §8.

Built under full autonomy ([ADR-0003](../adr/ADR-0003-full-autonomy-to-2.0.md)); no in-product AI
([ADR-0008](../adr/ADR-0008-no-in-product-ai.md)) — every "translation" and "check" here is
**deterministic** (template/rule-driven), which is the whole point.

---

## 1. The thesis: from "runs automations" to "asserts desired state"

Today Nexus *runs* governed automations. The 4.0 thesis is that an enterprise control plane must
**continuously assert that reality matches an intended, declared state** — and prove it to humans
of every technical level. Five mechanisms make that real, and they reinforce each other:

```
   CMDB Schema + Lineage ──defines──▶ what "healthy / correct" means (the contract)
            │
            ▼
   Idempotency + Compliance ──asserts──▶ desired vs observed, re-runnable, drift as a first-class signal
            │
            ▼
   Deterministic Pinning ──guarantees──▶ the right workflow is bound to the right CI, always
            │
            ▼
   Multi-audience Review ──authorizes──▶ humans (tech / non-tech / exec) approve before enforcement
            │
            ▼
   GitOps Backbone ──versions+backs──▶ all of the above as auditable, revertable config-as-code
```

The bridge that makes it usable: the **automation team authors precise, idempotent, plain-language
atomic building blocks once**; **operators/engineers compose** them; **reviewers/execs approve**
audience-appropriate summaries; **the platform guarantees and re-asserts** the result. No manual
changes; consistent, deterministic tagging/naming/lineage everywhere.

---

## 2. Pillar A — CMDB Schema & Lineage System  (M24)

**Seed:** a strong CI lineage checker and schema system; easily define/update/maintain what makes
up a CI's lineage per CI type; field-driven; plugs into CI lookups; drives how CMDB CIs are defined.

**Expansion.** Introduce a **CI Type Schema Registry** — schema-as-data (the same proven pattern as
`nexus-theme/v1` and `node_specs`, validated deterministically, admin-editable, no AI):

- **Field schema per CI type** (VM, Datastore, Cluster, Volume, BackupPolicy, Application, Host…):
  each field has `name, label, datatype, required, allowed_values|regex, default, sensitivity`. Tags
  are first-class (required tags, allowed values, naming patterns).
- **Lineage spec per CI type** — a *typed relationship contract*: required upstream/downstream
  relationships with cardinality (a `VM` must resolve `host→cluster→datacenter`, a `datastore`,
  a `backup_policy`, an `owner/team`, an `environment`). Lineage is the graph of what *makes a CI
  whole*, not just its own fields.
- **Lineage / Health Checker** — given a CI (fetched via the ServiceNow ACL connector), evaluate it
  against its type's field schema **and** lineage spec → a **CI Health Report**: missing/invalid
  fields, broken/missing/orphaned relationships, tag/naming non-compliance, plus a **health score**
  and **remediation hints**. Pure, deterministic, unit-tested.
- **Schemas are versioned** and admin-maintained through a **CMDB Schema Studio** (define/edit CI
  types + lineage rules with a live deterministic validator), mirroring Theme Studio.

**Value thesis.** This converts the CMDB from "a place you look things up" into **"a contract the
platform enforces."** "Healthy CI" stops being tribal knowledge and becomes machine-checkable — the
precondition for deterministic pinning (Pillar D) and for review packets (Pillar C) to compute real
impact. It also *drives* how CIs should be defined, so new integrations declare their CI shapes once.

**Placement.** New bounded context **`cmdb`** (owns CI type schemas, lineage specs, the health
checker). The ServiceNow connector remains the **ACL** that fetches raw CI data; `cmdb` interprets
it against schemas. The existing `lifecycle_validation` gate ([ADR-0006](../adr/ADR-0006-lifecycle-validation-gate.md))
becomes a *consumer* of the health checker (richer than today's CMDB-consistency check).

**Surfaces.** CI **health badges** in CMDB-lookup nodes and every target picker; a **Lineage
Explorer** (the CI + its required relationships as a graph, gaps highlighted).

---

## 3. Pillar B — Idempotency & Compliance Engine  (M25)

**Seed:** ALL automation must be idempotent and re-runnable for compliance; run anything anytime to
see potential impact, config drift, diffs.

**Expansion.**
- **Idempotency contract.** Every connector action and catalog building block declares an
  **idempotency class**: `idempotent` (converges to desired state, safe to re-run), `check_only`
  (read/plan), or `non_idempotent` (must be guarded — flagged and discouraged). A validator surfaces
  non-idempotent blocks; the catalog shows the class. This *forces the mandate into the contract*,
  not a hope.
- **Drift / compliance model.** A first-class **DriftReport** (desired vs observed, per-resource &
  per-field: `compliant | drifted | unknown`, with the reconcile action that would converge it).
  The connector port gains `evaluate_compliance()`; simulation adapters produce believable drift.
- **Compliance run intent.** Any template/workflow can run in **compliance mode** — a dry-run that
  yields an aggregated drift report + blast radius (Pillar A) **without mutating**. This generalizes
  the existing check-mode/diff into "assert, don't change, tell me the gap."
- **Continuous posture.** Reuse scheduling (M11) for **compliance sweeps** → a **compliance posture
  dashboard** (% of CIs/workflows in compliance, drift trend, top drifted). Drift opens **incidents**
  (M16). Drift becomes a managed signal, not a surprise.

**Value thesis.** Idempotency + compliance mode turns Nexus into a system that **continuously
asserts desired state** — the reconcile loop. It is the backbone that makes pinning (Pillar D)
meaningful (a pinned validator re-runs to assert), and it lets anyone preview impact/diff before any
real change.

**Placement.** Extend `execution_engine` + `connectors` (port + idempotency declaration + compliance
intent + DriftReport DTO). Posture aggregation can live in `observability`.

---

## 4. Pillar C — Multi-Audience Human Review & Executive Approval  (M26)

**Seed:** humans must approve workflows *set to run* (not just CI adds); normal vs standard change
governs when; an executive capability; review as a workflow, a clean markdown explanation, or a rich
flowchart (input → action → outcome in human language); **Technical / Non-technical** review modes;
translate technical → non-technical for managers who don't care if it's Terraform or Ansible.

**Expansion.**
- **Change classification drives review.** Each run is classified `standard` (pre-approved low-risk),
  `normal` (needs review/approval), or `emergency` (expedited) — derived deterministically from
  building-block risk tier, blast radius (Pillar A), targets (prod vs non-prod), and idempotency
  class (Pillar B). Policy-as-config maps classification → required reviewer levels.
- **The Change Review Packet** — before an approval-gated run, Nexus deterministically generates a
  *multi-representation* rendering of exactly what will happen:
  - **Technical:** the graph, each node's connector/action/resolved params, resolved targets, the
    plan/diff (Pillar B), blast radius (Pillar A).
  - **Non-technical / Executive:** a plain-language narrative composed from each building block's
    authored **plain summary** (`input → action → outcome` slots) in execution order — e.g. *"This
    change will: 1) snapshot 3 production VMs, 2) apply OS patches, 3) verify health. Target: prod-web
    (3 servers). Outcome: patched & rebooted, ~5 min downtime each. Risk: medium. Rollback: restore
    snapshot."* **No AI** — composed from authored templates + resolved variables.
  - **Flowchart:** a clean read-only flow (reuse `LogicFlow`) with each step labeled in human terms
    (what it gets, does, results in).
- **Audience toggle:** Technical / Non-technical / Executive buttons switch the rendering; Executive
  shows outcomes/risk/impact only.
- **Run-level approval gate** (extends change_management + approval_gate): an approval-required run
  enters `pending_approval`, generates the packet, routes per policy (multi-level: team lead → exec
  for high-risk), reviewers approve/reject/request-changes with comments; the run resumes on approve.
- **CI-change path:** adding/modifying a CI runs the health checks (Pillar A) **and** a human
  approval when policy requires.

**Value thesis & the key insight.** The packet is the bridge the operator described — but it only
works if **building blocks carry an authored plain-language summary** (new catalog/node metadata).
That forces the automation team to declare *intent in plain English once*; every workflow built from
those blocks then gets **free, executive-ready documentation and review packets**. High capability,
low recurring effort — exactly "value, not complexity."

**Placement.** Extend `change_management`; add a deterministic **ReviewPacket builder** slice. Add an
**executive** capability to RBAC. Frontend: packet viewer with audience toggle in Governance + a
reviewer queue.

---

## 5. Pillar D — Deterministic Policy & Workflow Pinning  (M27)

**Seed:** a management page to set deterministic rules pinning a guaranteed workflow to a CI/object
— e.g. every `VM` gets a pinned tag+CMDB validator; a `VM` tagged `DR-Tier=0` gets a pinned
"Zerto DR VPG" workflow. Expand meaningfully.

**Expansion.** A **Pinning Rule = (selector → guaranteed workflow + trigger + enforcement mode +
priority)**:
- **Selector:** predicates over CI **type + tags + fields** (built from the Pillar A schema), e.g.
  `type=VM`, or `type=VM AND tag:DR-Tier=0`, or `field:environment=prod`.
- **Guaranteed workflow:** a published workflow to run/assert.
- **Trigger:** on-CI-create, on-CI-change, on-schedule (compliance cadence), or on-demand.
- **Enforcement mode:** **assert** (compliance/dry-run, report drift), **enforce** (auto-reconcile,
  subject to review policy in Pillar C), or **gate** (block the triggering change until the pinned
  workflow passes its health/compliance check).
- **Precedence & composition:** rules carry priority and compose; a **ruleset can be dry-run against
  the current CMDB** to preview coverage *before* enabling.

**Value thesis — guarantee + coverage, not just triggers.** The management page's headline question
is **"what is guaranteed about my estate, and where does reality not match?"** It shows, per rule,
*matched CIs / compliant / drifted* and the would-be actions. This is management-by-invariant: admins
declare invariants ("every Tier-0 VM has a Zerto VPG"; "every VM is continuously tag/CMDB-validated")
and the platform **continuously asserts** them (Pillar B), **enforces** through review (Pillar C),
and surfaces the gap. It ties the whole line together and is the antithesis of "hope someone runs it."

**Placement.** New `determinism` (policy-pinning) slice: PinningRule model + matcher (uses `cmdb`
selectors) + a **reconciler** that, per trigger, evaluates rules → a pinned-actions plan
(assert/enforce/gate), launching compliance runs (Pillar B) or review-gated enforce runs (Pillar C),
on a scheduled cadence (M11), opening incidents on drift (M16). Frontend: a **Determinism /
Guardrails** management page with a schema-driven selector builder + coverage/impact preview.

---

## 6. Pillar E — GitOps Backbone (backend Git versioning & sync)  (M28)

**Seed:** the agnostic system should sync and do its own versioning, push/pull as backup & a system
dependency; point at git repos; version saved workflows, config, references; GitOps.

**Expansion.** Everything in Nexus is already data (workflows, CI schemas, pinning rules, themes,
validation policies, change templates, schedules). Make it **config-as-code in Git**:
- **Canonical serialization** — deterministic on-disk layout (stable key ordering, no embedded
  timestamps) so diffs are meaningful and **re-export of unchanged config is a no-op** (idempotent).
- **Push / backup (system of record + DR):** on artifact change (and on a schedule), commit the
  canonical serialization to a configured Git repo with an **audit commit message** (who/what/why).
  Default is a **local repo** (Docker volume / bare repo) — *guardrail: official git only, no paid /
  remote services; the operator may point at any reachable remote they configure.*
- **Pull / reconcile (GitOps, optional):** treat a repo as **desired config state**; diff against
  live; apply with approval (Pillar C). Makes environment **promotion** and **rollback** trivial
  (check out a prior commit / a peer environment's repo).
- **Per-artifact history:** view history, diff, and **restore** any prior version of a workflow,
  schema, ruleset, etc.
- **Repo strategy (docs in Pillar F):** the **platform-config repo** is separate from the
  **infracode pillar repos** (the actual Ansible/Terraform/etc. content) — both documented.

**Value thesis.** Deterministic, auditable, **revertable** configuration + DR backup + environment
promotion, without bespoke export/import. The existing admin export bundle (K45) becomes the seed of
a real versioning backbone. Guardrails keep it safe: local-first, optional pull, official tooling.

**Placement.** New `gitops`/`config_versioning` platform capability behind a `VersioningPort`
(adapter: local git via official tooling). Auto-commit hooks on save + scheduled sync. Admin page:
configure repo, sync status, per-artifact history/diff/restore, "back up now".

---

## 7. Pillar F — Documentation & Repo/Org Strategy  (M29)

**Seed:** exact documentation on the whole platform — features, capabilities, how to use; the
concept of atomic automation rolled up into a governed, unified, vendor/platform-agnostic tool that
ops/eng *consume*; the "bridge"; no manual changes; deterministic tagging/naming. Plus org/repo
strategy docs — pillar/mono repos per integration (infracode_ansible, infracode_terraform,
infracode_snow, infracode_pure, infracode_cisco).

**Expansion.** A real `docs/` tree, partly **authored** and partly **generated from the system's own
metadata** so it can't drift:
- **Concepts:** the atomic-automation → governed-composition philosophy; the two-altitudes bridge;
  determinism / idempotency / no-manual-changes mandate; value per persona.
- **Persona guides:** automation engineer (author atomic blocks; declare idempotency + plain summary
  + CMDB schema), operator (compose & run), reviewer/exec (review packets), admin (schemas, pinning,
  gitops, policy).
- **Feature guides** per surface, including the new M24–M28 surfaces.
- **Org & repo strategy:** the **infracode pillar/mono-repo-per-integration** model
  (ansible/terraform/snow/pure/cisco) — structure, naming, branching, ownership; how Nexus
  references/syncs them; separation from the platform-config repo (Pillar E); the **tagging & naming
  conventions** that make everything deterministic.
- **In-app docs:** a searchable `/docs` surface (reuse the Markdown renderer), linked from the shell
  and the command palette; **reference sections generated** from catalog plain summaries, CMDB
  schemas, and pinning rules.

**Value thesis.** Docs are the manual — but generated reference docs stay accurate, and an in-app,
searchable surface makes capability discoverable at the moment of need.

---

## 8. Delivery plan (milestones → epics → stories)

Milestones map to **releases** (`CLAUDE.md §7`); each story = branch → spec/ADR → TDD → green CI →
merge. Dependencies: A→(B,C); (A,B)→D; (A,D)→E; F throughout; G last.

| # | Milestone (epic) | Depends on | Releases toward |
| --- | --- | --- | --- |
| **M24** | CMDB Schema & Lineage System (Pillar A) | — | `v4.0` line start |
| **M25** | Idempotency & Compliance Engine (Pillar B) | M24 |  |
| **M26** | Multi-Audience Review & Executive Approval (Pillar C) | M24 (impact), existing change-mgmt |  |
| **M27** | Deterministic Policy & Workflow Pinning (Pillar D) | M24, M25 |  |
| **M28** | GitOps Backbone (Pillar E) | M24, M27 (artifacts to version) |  |
| **M29** | Documentation & Repo/Org Strategy (Pillar F) | M24–M28 (document as built) |  |
| **M30** | Admin/Integrator UAT & hardening (Pillar G) | M24–M29 | cut `v4.0.0` |

Story-level breakdown is maintained as GitHub issues under each milestone (the bite-size chunks),
each carrying its own acceptance criteria + the design brainstorm from the matching pillar above.
ADRs are written as each milestone's key decision is made (planned: ADR-0009 CMDB schema/lineage
context, ADR-0010 idempotency & drift model, ADR-0011 multi-audience review + run approval, ADR-0012
deterministic pinning/reconcile, ADR-0013 GitOps config backbone).

## 9. Guardrails carried into 4.0
- **No in-product AI** (ADR-0008): all translation/classification/checking is deterministic.
- **No paid/remote services by default**; GitOps defaults to a local repo; official tooling only.
- **No secrets in the repo or any agent-read file**; Git audit messages carry actor, not credentials.
- **Idempotency is mandatory** for any building block that mutates; non-idempotent blocks are flagged.
- **Simulation only**: drift, CMDB data, and git remotes are simulated/local; no real backends.

# Feature guides — by surface

Concise how-to for every Nexus surface. Reach any of them via the nav rail or the **⌘K / Ctrl-K**
command palette.

## Dashboard
Fleet pulse: run counts (running/succeeded/failed/pending), success rate, avg duration, a
**Needs-attention** card (workflows awaiting review, failed runs, stale automations) and **Favorites**.

## Catalog
The library of approved **atomic building blocks**. Faceted by domain/vendor; each card shows risk +
type + duration. The detail drawer has **Overview** (incl. the plain-language "In plain language"
summary + idempotency chip), **Parameters**, and an animated **Logic Flow**. Actions: **Run** (with
check-mode), and **Check compliance** (drift report, no mutation).

## Canvas
Compose workflows from nodes. Add an **Automation Task** and use **Start from catalog item** to
pre-fill connector/action/params from a vetted block; add a **Sub-Workflow** to reuse a saved/approved
workflow. Inline lint flags structural problems. **Dry run** plans the whole DAG (nothing mutates);
**Run** executes (blocked by approval if the policy requires). Save → **Submit for review**.

## Library
Saved workflows across teams: ownership, usage, success rate, review state. Drill in for run history,
**replay**, and **retry**; submit drafts for review.

## Console
Live, streamed run output (ANSI), with an in-run **filter** and **download log**.

## Incidents
Failures and **drift** auto-open incident cards (New → Triage → Investigating → Resolved) with a
failure-mode tag and "similar past failures"; one click **converts to a remediation workflow**.
A trends row shows MTTR + top failing automations.

## Compliance
Estate **posture** from scheduled drift sweeps: % compliant, drifted counts, top-drifted, a trend
sparkline, and an admin **Run sweep now**. Drift reports show desired-vs-observed per field + reconcile.

## Approvals
The reviewer queue. Open a pending run/CI-change, switch the **Technical / Non-technical / Executive**
audience, read the packet + flowchart, and **approve / reject / request changes**.

## Determinism & Guardrails
Author **pinning rules** (selector → guaranteed workflow + trigger + enforcement: assert/enforce/gate)
with a schema-driven selector builder. The **coverage** panel answers "what is guaranteed about my
estate, and where does reality not match?" — matched CIs, compliant vs drifted, missing-workflow warnings.

## CMDB Schema Studio & Lineage Explorer
**Schema Studio** (admin): define each CI type's fields, required tags, naming pattern, and lineage
(typed required relationships) — validated deterministically on save. **Lineage Explorer**: look up a
CI to see its health score, lineage with gaps highlighted, and remediation hints.

## GitOps
Config-as-code: repo status, **Back up now** (admin), commit **history** + **diff**, **restore** a
prior version, and a **pull-preview** (repo vs live). Local git only.

## Governance
Workflow review inbox (approve/changes/reject), the validation-policy editor, automation
review/pruning, and the **change calendar** (from the simulated ServiceNow CMDB) with conflict flags.

## Admin
Your access + RBAC matrix, platform status, connector registry, data export, and links to the CMDB,
Guardrails, and GitOps governance surfaces.

## Accessibility & Theme Studio
Color mode (system/light/dark + sundown + per-area overrides), density, dyslexia font, text scale,
10 themes; **Theme Studio** authors themes with a deterministic WCAG validator.

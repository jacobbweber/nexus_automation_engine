# Vision — Operator Experience (3.0 fresh pass)

A from-scratch rethink of Nexus from the **infra-ops operator** mindset (the person who runs and
composes automation all day), plus the **automation-admin** who governs it. Built on the 1.0/2.0
engine; this pass is about scale, comprehension, governance, and "bells & whistles" that make the
platform genuinely useful at **thousands** of automations.

## The operator's real jobs-to-be-done
1. **Find** the right capability fast (out of thousands) — not scroll a wall.
2. **Understand** it before running — what it does, blast radius, risk, prerequisites.
3. **Run** it safely — guided, dry-run-first, with live proof and rollback paths.
4. **Compose** vetted capabilities into bigger workflows — like Lego — under governance.
5. **Recover** when things fail — capture, triage, remediate.

## Pillars

### 1. Service Catalog at scale (never a dropdown)
- **Taxonomy:** domain (Compute/Storage/Backup/Network/ITSM/Security) → vendor (VMware/Pure/
  Cohesity/ServiceNow/Ansible) → capability. Tags, risk tier, est. duration, owner.
- **Discovery:** type-ahead search, faceted filters, **collections**, favorites/recents/"my
  queue", popularity + success-rate, and a **Ctrl-K command palette** to find-and-run anything.
- **Atomic vs orchestrated** are visually distinct; orchestrated items show their phase count.

### 2. Understand-before-you-run (automation detail)
- README/markdown docs, parameter schema, **prerequisites, risk, est. duration, owner**, last-N
  runs + success rate, related CIs.
- **Logic Flow tab:** an animated SVG that visualizes the automation's phases / DAG, and animates
  the live execution trace (node-by-node) — the centerpiece "wow."
- **Blast-radius preview:** which CMDB CIs/services this run would touch (impact analysis).

### 3. Governed Lego composition (extends 2.0 approval)
- Atomic, *controlled* capabilities (e.g. `Delete Datastore`, `Eradicate Pure Volume`) are
  publishable building blocks with risk gating.
- Operators compose on the canvas → **submit for review** → workflow-admins approve/reject with
  comments → published as a catalog item. Lifecycle: draft → submitted → in_review →
  approved/changes_requested/rejected → published. An **approvals inbox** for reviewers.
- Promotion across environments; ownership; review history as audit.

### 4. Incident / Error Kanban
- Every failed run/workflow auto-creates an **incident card** in a backlog board
  (New → Triage → Investigating → Resolved), linked to the failing run + logs.
- One click: **convert incident → remediation workflow** on the canvas.
- Trend view: top failing automations, MTTR.

### 5. A believable, large simulated catalog
Realistic content so the UX has substance — VMware VCF 9, Pure Storage (Ansible), Cohesity,
ServiceNow CMDB/RITM/CHG, plus generic Ansible/Terraform/script. Rich metadata per item.

## My additions (challenging/extending the seed ideas)
- **Guided "runbook" mode** with step confirmations for high-risk atomic ops.
- **Dry-run/plan everywhere** + diff/impact preview before commit.
- **Success-rate analytics & MTTR** per automation and per domain.
- **Parameter presets / saved targets** ("prod-east fleet", "PCI hosts").
- **Notifications feed** (run finished, approval requested, incident opened).
- **Convert incident → remediation**, and **"similar past failures"** suggestions.
- **CMDB-driven target pickers** everywhere (already have the connector).

## Delivery milestones (3.0 line)
- **M13** — Connector ecosystem + rich catalog metadata + large realistic seed (VCF/Pure/
  Cohesity/SNOW). *(backend)*
- **M14** — Catalog-at-scale UX: faceted search/grouping, automation detail w/ docs + animated
  Logic-Flow tab. *(frontend)*
- **M15** — Governed workflow submission/review + approvals inbox. *(full stack)*
- **M16** — Incident/Error Kanban (auto-capture) + convert-to-remediation. *(full stack)*
- **M17** — Command palette, favorites/recents, success-rate analytics, notifications. *(polish)*

Each milestone: branch → TDD → green CI → merge; tag a 3.x release as the line matures.

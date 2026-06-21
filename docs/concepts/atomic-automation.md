# Atomic automation → governed composition

## The problem
Enterprise automation is **dispersed and heterogeneous** — Ansible controllers, Terraform state,
jump-box scripts, plus systems of record (ServiceNow), vaults (CyberArk), observability (Dynatrace).
Each speaks its own protocol and fails its own way. Two failure modes result:

- **Automation teams** build precise, well-tested automations — but they end up siloed, re-invented,
  and run inconsistently (different people, different parameters, different days → different results).
- **Operations & engineering** need to *get things done* but can't safely touch every backend, so
  work becomes manual, ad-hoc, and undocumented.

## The bridge
Nexus splits the problem at the right seam:

- **Atomic building blocks** — the automation team authors *small, precise, idempotent* units (an
  Ansible job template, a Terraform apply, a CMDB lookup, a Pure volume snapshot). Each block is
  **approved, versioned, and declares its contract**: its idempotency class, a plain-language summary
  (input → action → outcome), the CI type it targets, its risk. Authored **once**.
- **Governed composition** — operators/engineers **compose** those vetted blocks on the canvas into
  bigger workflows (Lego-style), *without* needing to know Terraform vs Ansible vs a JSON payload.
  They define the *process*; Nexus runs the backend details.

This is the "two altitudes, one product" philosophy: a guided, low-friction surface for consumers,
a deep extensible plane for the automation team — both powered by the same domain.

## Why this is the best of both worlds
- **Precision + consistency** (from the automation team's atomic blocks) **+ low-effort consumption**
  (from composition by ops/eng).
- **No manual changes**: every action goes through a vetted block, so it's done the same way no matter
  who runs it or where.
- **Deterministic by construction**: tagging, naming, lineage, idempotency, and review are declared
  and enforced — not left to discipline.

## How a block becomes a guaranteed outcome
1. **Author** the atomic block (catalog template): connector + action + survey + **idempotency** +
   **plain summary** + **CMDB ci_type**.
2. **Compose** it into a workflow on the canvas; **submit for review**.
3. **Classify & review**: Nexus classifies the change and generates a multi-audience review packet;
   the right reviewers approve.
4. **Publish** the workflow; optionally **pin** it as a guarantee for a class of CIs.
5. **Assert** continuously (compliance mode) — drift becomes an incident; **GitOps** versions it all.

See also: [the determinism & idempotency mandate](determinism-mandate.md).

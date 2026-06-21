# Nexus Automation Engine — Documentation

Nexus is an **automation control plane**: a governing layer above many backend automation systems
(Ansible, Terraform, VMware, Pure, Cohesity, ServiceNow, …) that presents one secure, composable,
**vendor-agnostic** surface. The automation team authors precise, idempotent **atomic building
blocks**; operators and engineers **compose** them into governed workflows; reviewers and executives
**approve** audience-appropriate summaries; and the platform **continuously asserts** the result.

> No manual changes. Consistent, deterministic tagging / naming / lineage everywhere. No in-product AI
> ([ADR-0008](../specs/adr/ADR-0008-no-in-product-ai.md)).

## Start here
- **Concepts**
  - [Atomic automation → governed composition](concepts/atomic-automation.md) — the core idea & the bridge.
  - [The determinism & idempotency mandate](concepts/determinism-mandate.md) — why and how.
- **Personas** — [who does what](personas/personas.md) (automation engineer · operator · reviewer/exec · admin).
- **Feature guides** — [per-surface how-to](guides/surfaces.md).
- **Org & repo strategy** — [infracode pillar repos + conventions](strategy/infracode-repos.md).

## The governance lifecycle (how it all fits)

```
author atomic block  →  compose workflow  →  classify & review  →  publish
        │                                          │
        ▼                                          ▼
  declare: idempotency,                    pin a guarantee (rule) ──► continuously assert (compliance)
  plain summary, CMDB schema                      │                         │
                                                  ▼                         ▼
                                          enforce via review        drift → incident → remediate
                                                  │
                                                  ▼
                                   everything versioned in Git (config-as-code)
```

## The v4.0 capabilities (Deterministic Governance)
- **CMDB Schema & Lineage** — CIs are a schema-enforced contract with a deterministic health checker.
- **Idempotency & Compliance** — every block declares re-run safety; run anything in compliance mode
  to see drift; scheduled sweeps + posture + incidents.
- **Multi-audience Review** — technical / non-technical / **executive** review packets + run approval.
- **Deterministic Pinning** — guarantee a workflow for matching CIs; coverage shows the gap.
- **GitOps backbone** — config-as-code: versioned, diffable, restorable, backed up.

See [`specs/00_foundation/vision_deterministic_governance.md`](../specs/00_foundation/vision_deterministic_governance.md)
for the full design and the [glossary](../specs/00_foundation/glossary.md) for vocabulary.

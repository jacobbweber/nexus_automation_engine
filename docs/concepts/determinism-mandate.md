# The determinism & idempotency mandate

Nexus treats configuration management as **continuously asserting a declared, intended state** —
not "running scripts." Four rules make that real.

## 1. No manual changes
Every change to a system goes through a **vetted atomic block** (or a workflow composed of them).
Nothing is done by hand on a target. This guarantees that *how* a change happens is identical
regardless of who initiates it or when.

## 2. Everything is idempotent (and re-runnable for compliance)
Every connector action and building block declares an **idempotency class**:
- `idempotent` — converges to desired state; safe to re-run.
- `check_only` — reads / plans; never mutates.
- `non_idempotent` — mutates and is *not* safe to blindly re-run (flagged; discouraged).

Because blocks are idempotent, you can **run anything, anytime, in compliance mode** — a dry-run that
reports drift (desired vs observed, per field, with the reconcile action) **without mutating**.
Scheduled compliance sweeps snapshot estate **posture** and open **incidents** on drift.

## 3. Deterministic by contract (no AI)
Every "translation" and "check" is rule/template-driven, never AI ([ADR-0008](../../specs/adr/ADR-0008-no-in-product-ai.md)):
- **CMDB schema + lineage** define what a healthy CI is; the health checker is deterministic.
- **Change classification** (standard/normal/emergency) and **review packets** (technical /
  non-technical / executive) are composed from declared metadata.
- **Pinning rules** and the **reconciler** are pure functions over rules + CIs.
- **Config serialization** is canonical (stable key order, no volatile timestamps) so Git diffs are
  meaningful and re-serialization of unchanged config is byte-identical.

The same inputs always produce the same outputs — classifications, packets, drift, coverage, commits.

## 4. Declared, enforced, and versioned
- **Tagging / naming / lineage** are declared in the CMDB schema and enforced by the health checker.
- **Guarantees** are declared as pinning rules ("every DR-Tier-0 VM has a Zerto VPG") and the
  coverage view shows where reality doesn't match.
- **All config is versioned in Git** (config-as-code) — auditable, diffable, revertable, backed up.

## Why it matters
Determinism turns "we hope it's consistent" into "we can prove it, continuously, and show the gap."
That is the difference between automation that *runs* and a control plane that *governs*.

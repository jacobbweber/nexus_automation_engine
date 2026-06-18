# Spec Conventions — Nexus Automation Engine

How specifications, decisions, and terminology are written and maintained in this repo. This is
the meta-spec; everything under `specs/` follows it.

---

## 1. Directory map

```text
specs/
├── 00_foundation/        # cross-cutting ground truth
│   ├── _conventions.md   # this file
│   ├── architecture.md   # DDD bounded contexts + vertical-slice rules + topology
│   ├── glossary.md       # living glossary ($GLOSSARY) — terms + mental models
│   └── rbac.md           # (planned) RBAC & entitlement matrix
├── adr/                  # Architecture Decision Records ($ADR_DIR), append-only
│   └── ADR-XXXX-*.md
├── 01_identity_access/   # per-bounded-context specs (Why/What)
├── 02_canvas_orchestration/
│   └── canvas_orchestration.md   # ★ the visual canvas engine
├── 03_execution_engine/
├── 04_connectors/
└── 05_catalog/
```

Spec numbering groups by bounded context (see `architecture.md`). Numbers are organizational,
not a priority or build order.

## 2. Why/What vs How separation

- **Domain specs** (per context) describe **Why** (the business reason) and **What** (the
  contract: entities, invariants, API shapes, UX behavior). They are vendor-neutral.
- **How** (implementation detail — library choices, file wiring) lives in code and, where a
  choice is significant, in an **ADR**. Don't bury architectural decisions inside prose specs.

## 3. Spec document shape

Every context spec carries, in order: **Goal** · **Use cases & value** · **Domain model**
(entities, value objects, invariants) · **Application contracts** (commands/queries, API/WS) ·
**UX behavior** (if it has a surface) · **Acceptance criteria** · **Open questions**.

## 4. Spec-first contract

Code follows spec, never the reverse. Changing a contract means editing the spec **in the same
PR** that changes the code, and the commit body references the spec path. If a change
contradicts an *approved* spec, that is a `[GATE]` per `CLAUDE.md §2` — propose the direction
change first.

## 5. ADR conventions (referenced by `CLAUDE.md §5`)

- ADRs live in `specs/adr/` named `ADR-NNNN-kebab-title.md` (zero-padded, monotonic).
- **Append-only. Never edit an accepted ADR's decision** — write a new ADR that supersedes it,
  and mark the old one `Status: Superseded by ADR-MMMM`.
- Required sections: **Status** (Proposed / Accepted / Superseded) · **Context** · **Decision**
  · **Consequences** (good and bad) · **Alternatives considered**.
- Record an ADR whenever a choice is significant or hard to reverse (architecture, data
  contract, a cross-context boundary, a vendor-abstraction seam).

## 6. Glossary discipline

The glossary (`$GLOSSARY`) is the single source of truth for project vocabulary. Per
`CLAUDE.md §9`, terminology drift is corrected proactively against it, and abstract concepts get
a **mental model** (what it is *and how it flows*), not just a one-liner. When a term in a spec
or from the operator is loose or wrong, fix it and update the glossary.

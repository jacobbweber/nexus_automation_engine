# ADR-0001 — Domain-Driven Design organized as Vertical Slices

**Status:** Accepted (2026-06-18)

## Context
Nexus is a vendor/platform-agnostic automation control plane whose entire value is **isolating
change**: adding a backend connector or a canvas node type must not ripple across the system. It
serves two very different audiences (deep admin/governance vs. simple operator) over one domain.
The source blueprint proposed a layers-by-technology layout (`models/`, `schemas/`, `services/`,
`api/`), which spreads each capability across the whole tree and couples features through shared
technical layers.

## Decision
Adopt **Domain-Driven Design with bounded contexts implemented as vertical slices**. Each context
(`identity_access`, `automation_catalog`, `orchestration_canvas`, `execution_engine`,
`connectors`, `observability`) owns its full stack in one folder — `domain/` (pure rules),
`application/` (use cases), `infrastructure/` (adapters), `api/` (REST/WS), `tests/` — with
dependencies pointing inward (Hexagonal / Ports & Adapters). Cross-context communication only via
published application contracts or the `shared_kernel`. Vendor specifics are confined to the
`connectors` Anti-Corruption Layer. The frontend mirrors the slices as feature folders. Full
detail in [`specs/00_foundation/architecture.md`](../00_foundation/architecture.md).

## Consequences
**Good:** change is localized; each slice is independently testable; the vendor-agnostic seam is
structural, not aspirational; the two-audience product maps cleanly onto context + feature
boundaries; onboarding reads one slice, not the whole tree.
**Bad / costs:** more upfront structure and some duplication across slices (deliberate — favors
decoupling over DRY); requires discipline to not reach across context internals; the shared
kernel must be guarded against becoming a dumping ground.

## Alternatives considered
- **Layers-by-technology (blueprint default):** rejected — couples features, fights the
  isolate-change goal.
- **Single modular monolith without explicit contexts:** rejected — boundaries blur over time.
- **Microservices from day one:** rejected — premature operational complexity for a POC; the
  slice boundaries leave that door open later without committing now.

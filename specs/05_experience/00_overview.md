# Experience Architecture — Overview

The cross-cutting design spec for the Nexus frontend: a token-driven design system, a
mode/area/theme engine, a theme studio, and a per-surface feature-depth program. It builds on
[`vision_operator_experience.md`](../00_foundation/vision_operator_experience.md) and is governed
by [ADR-0007](../adr/ADR-0007-experience-and-theming-architecture.md).

## Goal

Make Nexus calm, legible, and confidence-inspiring for the people who run automation all day —
without ever sacrificing the operational legibility (status, blast radius, run state) that an
automation control plane lives or dies by.

## Audience

- **Infra-ops operators** — find, understand, run, compose, and recover automation. Expertise
  ranges from a first-week operator to a senior SRE. The UI must be *teachable to the novice and
  fast for the expert* at the same time.
- **Automation-admins** — govern: review/approve workflows, edit policy, manage RBAC, watch fleet
  health.

This is **not** a consumer/broad-audience product. There is no child/teen surface. "Accessible and
calm" here means *reducing cognitive load during high-stakes operational work* (change windows,
incident bridges, bulk fleet actions) and meeting accessibility standards for the real operators on
ops teams — including low-vision, colorblind, and ADHD/ADD operators.

## Core principles

1. **Layout is locked; only skin and depth vary.** Themes and area-context retints change color,
   warmth, radius personality, density, and motion — never structural furniture. This is what makes
   a generated/edited theme safe and keeps the platform coherent across surfaces.
2. **One token contract, many resolvers.** Every visual value resolves through a single semantic
   token layer. Mode (dark/light), active area, and theme are *cascade layers* over that contract —
   never parallel styling systems.
3. **Operational legibility is sacred.** Status colors (running / ok / warn / failed / skipped),
   blast-radius emphasis, and run-state are *protected semantics*. A theme may shift their hue
   family but must keep them mutually distinguishable, colorblind-safe, and **always paired with an
   icon or shape** — never color-only. Area accents must never collide with status semantics.
4. **Calm under pressure, graceful when degraded.** No alarm-fatigue, no punitive language,
   non-blocking notifications, and honest offline/degraded states when a connector or container is
   unavailable.

## The resolution cascade (how dark/light + area + theme co-exist)

The root element carries three orthogonal attributes; CSS `@layer` ordering makes precedence
deterministic, so *every combination is valid by construction*:

```html
<html data-mode="dark" data-area="canvas" data-theme="signal" data-density="comfortable">
```

```css
@layer reset, primitives, semantic, mode, area, theme, density, a11y;
```

- **primitives** — raw palette ramps + scales (never consumed directly by components).
- **semantic** — the *contract*: `--bg`, `--surface`, `--text`, `--accent`, status tokens…
  Components consume **only** these.
- **mode** — remaps semantic tokens to the dark/light ramp stop.
- **area** — overrides *accent family + ambient tint + persona/assistant hue only* for the active
  surface (Dashboard/Catalog/Canvas/Library/Console/Incidents/Governance/Admin).
- **theme** — a built-in or user/studio theme remaps the same semantic keys (validated; cannot
  touch layout or status distinguishability).
- **density** — `cozy | comfortable | compact` scales spacing/typography multipliers.
- **a11y** — highest layer: `prefers-reduced-motion`, `prefers-contrast`, forced-colors, dyslexia
  font, text-scale. **Always wins** over theme and area.

Because the layers are orthogonal over one contract, "Terminal theme + Console area + dark +
compact + reduced-motion" needs zero special-casing.

## Document set

- [`01_design_system.md`](01_design_system.md) — design tokens (exact values), component spec,
  accessibility, protected status colors.
- [`02_theming.md`](02_theming.md) — mode engine, area-context overrides, the 10 built-in themes,
  the Theme Studio pipeline (schema, validation, optional local-model assist, Docker volumes).
- [`03_feature_depth.md`](03_feature_depth.md) — deep feature expansion for every Nexus surface.
- [`04_roadmap.md`](04_roadmap.md) — the ordered implementation roadmap (the GitHub issue sequence).

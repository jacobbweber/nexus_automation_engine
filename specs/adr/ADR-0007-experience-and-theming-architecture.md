# ADR-0007 — Token-driven experience & theming architecture

**Status:** Accepted (2026-06-19) — the AI-assist provisions (optional local-model theme assist and
the optional Assistant) are **superseded by [ADR-0008](ADR-0008-no-in-product-ai.md)** (no in-product
AI/LLM). The token contract, layered resolvers, themes-as-data with server-side deterministic
validation, protected status semantics, and accessibility-as-top-layer all stand.

## Context

The Nexus frontend works but lacks depth, accessibility, and a coherent visual system. We want:
a system-wide dark/light engine with per-area retinting; a set of built-in themes plus a way for an
operator to author their own; and a large feature-depth program across every surface. The hard
constraint for an **automation control plane** is that operational legibility — run status, blast
radius, risk — must never be compromised by theming, and the audience is infra-ops operators and
automation-admins (novice → senior SRE), not a broad consumer base.

A naïve "theme = arbitrary CSS" approach would let a theme break layout or make `failed` runs
indistinguishable from `ok` — unacceptable. We need theming power that is *safe by construction*.

## Decision

Adopt a **single semantic token contract** consumed by all components, with mode, active area,
theme, density, and accessibility expressed as ordered CSS `@layer` resolvers over that contract
(see [`specs/05_experience/00_overview.md`](../05_experience/00_overview.md)). Specifically:

- **Layout is locked; only skin/depth vary.** Themes and area retints may only remap an
  **allow-listed semantic key set** — never selectors, layout, spacing scale, or fonts-by-file.
- **Protected status semantics.** `--run-*` and `--success/warn/danger/info` are validated for
  mutual distinguishability, colorblind safety, and are always paired with an icon/shape in
  components; **area accents may not collide with status colors**.
- **Themes are data** (`nexus-theme/v1` JSON), validated **server-side** by a deterministic gate
  (schema + key allow-list + WCAG/APCA contrast + protected-status check) before the frontend ever
  receives them. Built-ins ship read-only; user themes live on a writable Docker volume with
  hot-reload via an SSE `theme:changed` event.
- **Theme Studio is deterministic-first**; an **optional local-model assist** sits behind an adapter
  (same port pattern as connectors — local only, off by default, no paid services). Result safety
  never depends on the model; the validator is the gate.
- **Accessibility is the top layer** (reduced-motion, prefers-contrast, forced-colors, dyslexia
  font, text-scale) and always wins over theme/area. WCAG 2.2 AA is the baseline (AAA via the
  High-Contrast theme), enforced by an axe + contrast CI harness.

The full design tokens, the 10 built-in themes, the per-surface feature-depth program, and the
ordered build roadmap are specified under `specs/05_experience/`.

## Consequences

**Good:** every mode × area × theme × density × a11y combination is valid by construction (no
special-casing); themes can't break layout or operational legibility; accessibility is structural,
not bolted on; the TS-constants mirror of the tokens keeps canvas/SVG/chart rendering in sync with
CSS; the optional AI assist can't produce an unsafe theme.

**Bad / costs:** components must be disciplined to consume only semantic tokens (enforced by lint);
the protected-status validator and colorblind simulation add real work to the theme pipeline;
server-side theme validation adds a small platform surface (endpoint + watcher + volume); generating
tokens to two targets (CSS + TS) requires a build step.

## Alternatives considered

- **Per-component theming / ad-hoc CSS overrides:** rejected — drifts, can't guarantee
  accessibility or status legibility, unsafe for user/AI themes.
- **Theme = arbitrary CSS/Tailwind config:** maximal flexibility but can break layout and status
  semantics; fails the "safe by construction" requirement.
- **Browser-side theme validation:** rejected — would let unvalidated/inaccessible themes reach the
  UI; validation must gate before delivery, so it runs server-side.
- **Mandatory in-product AI for theming:** rejected — Nexus is local-first with no paid services
  and no shipped LLM; the deterministic Studio is the core, AI is an optional local adapter.

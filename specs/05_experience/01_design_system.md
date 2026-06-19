# Design System — Tokens, Components, Accessibility

The single source of truth for Nexus visual values. Components consume the **semantic token
contract** only; nothing hard-codes a hex value, radius, or pixel spacing.

## 1. Token layers

```
primitives   →  raw ramps + scales        (e.g. --clay-500, --space-4)   never used by components
semantic     →  the contract              (--bg, --surface, --accent…)   the ONLY thing components touch
mode/area/theme/density/a11y resolvers remap semantic keys (see 00_overview cascade)
```

Tokens ship twice: as CSS custom properties (runtime cascade) and as a generated TypeScript
constants module (for canvas SVG rendering, charts, and tests). The TS module is **generated from
the same source** so the two never drift.

## 2. Spacing (8pt grid, 4pt half-step)

```
--space-0:0  --space-1:4  --space-2:8  --space-3:12  --space-4:16
--space-5:24 --space-6:32 --space-7:48 --space-8:64 --space-9:96   (px)
density multiplier: cozy ×1.0 · comfortable ×0.86 · compact ×0.72
  (clamped so interactive targets never drop below 44px)
```

## 3. Radius (calm = generous; theme personality shifts the whole ramp one step)

```
--radius-xs:6 --radius-sm:10 --radius-md:14 --radius-lg:20 --radius-xl:28 --radius-2xl:36 --radius-pill:9999 (px)
defaults: inputs/buttons = md(14), cards = lg(20), modals/sheets = 2xl(36)
"sharp" personality −~40%; "soft/playful" +~30% (small controls capped at pill)
```

## 4. Typography (modular scale 1.2, base 1rem = 16px, fluid clamp on display sizes)

```
--font-ui:   "Inter var", system-ui, sans-serif
--font-read: "Source Serif 4", Georgia, serif      (long-form: README/docs/spec surfaces)
--font-mono: "JetBrains Mono", ui-monospace         (logs, params, code, canvas)
--font-dys:  "Atkinson Hyperlegible"                (a11y toggle)

--text-xs:.8rem/1.4   --text-sm:.875rem/1.45  --text-base:1rem/1.55
--text-md:1.125rem/1.5 --text-lg:1.25rem/1.4  --text-xl:1.5rem/1.3
--text-2xl:clamp(1.75rem,1.4rem+1.6vw,2.25rem)/1.2
--text-3xl:clamp(2.25rem,1.8rem+2.2vw,3rem)/1.15
weights 400/500/600/700 · headings tracking −0.01em · eyebrows +0.02em uppercase
max reading measure 68ch · effective body never < 15px
```

## 5. Elevation (warm-tinted, soft, low-spread — calm, never harsh black)

```
--shadow-0: none
--shadow-1: 0 1px 2px rgba(40,33,28,.05), 0 1px 3px rgba(40,33,28,.07)
--shadow-2: 0 2px 6px rgba(40,33,28,.06), 0 4px 12px rgba(40,33,28,.08)
--shadow-3: 0 8px 24px rgba(40,33,28,.10), 0 2px 6px rgba(40,33,28,.06)
--shadow-focus: 0 0 0 2px var(--bg), 0 0 0 4px var(--focus)
dark mode: subtler shadows + a 1px top inner highlight (--ring-hi) for lift
high-contrast theme: shadows OFF, 2px borders instead
```

## 6. Motion (gentle, decelerating; reduced-motion honored globally)

```
--dur-1:120 --dur-2:180 --dur-3:240 --dur-4:360 --dur-5:520 (ms)
--ease-out: cubic-bezier(.2,.8,.2,1)        (default)
--ease-spring: cubic-bezier(.34,1.56,.64,1) (small-scale only; disabled under reduced-motion)
prefers-reduced-motion → durations collapse to 0; opacity fades retained ≤80ms
```

## 7. Semantic color contract (the only keys components may use)

```
surfaces:  --bg --surface --surface-2 --surface-3 --overlay
text:      --text --text-muted --text-subtle --text-onAccent
lines:     --border --border-strong --divider
accent:    --accent --accent-hover --accent-active --accent-contrast --accent-soft
status:    --run-running --run-ok --run-warn --run-failed --run-skipped  (+ each *-soft)
generic:   --success --warn --danger --info  (+ *-soft)
system:    --focus --selection --link
area:      --area-accent --area-tint
```

### 7.1 Protected status semantics (Nexus-specific, non-negotiable)

`--run-*`, `--success/warn/danger/info` and blast-radius emphasis are **protected**. A theme may
shift their hue family but the validator (see `02_theming.md`) enforces:

- pairwise distinguishability of running/ok/warn/failed/skipped (ΔE + contrast minimums),
- colorblind safety (deuteranopia/protanopia/tritanopia simulation pass),
- they are **always accompanied by an icon/shape badge** in components, never color-alone,
- **area accents must not collide** with status colors (e.g. the Incidents area accent is a coral
  that is provably distinct from `--run-failed`), so an operator never misreads state.

## 8. Component spec (token-driven; teachable-yet-fast)

Each: anatomy · sizes · states · a11y. Representative set; all share the contract.

- **Button** — radius md; height 44 (compact 40, large 52); variants *primary* (area-accent fill),
  *soft* (`--accent-soft`), *ghost*, *quiet/text*, *danger*. Loading keeps the label + `aria-busy`;
  disabled never relies on color alone; active translateY(1px) suppressed under reduced-motion.
- **Input / Select / Textarea** — radius md, `--surface-2` field, focus → `--border-strong` + ring;
  **label always visible** (never placeholder-as-label); inline validation = icon + text +
  `aria-describedby`; optional voice/clear affordances.
- **Card** — radius lg, `--surface`, shadow-1, padding `--space-5`; interactive cards lift to
  shadow-2, are fully clickable, and keyboard-activatable; optional `--area-tint` header band.
- **Navigation rail** — 72px (icon) / 232px (expanded), per-area icon+label+accent dot; active area
  retints the whole shell; roving-tabindex keyboard nav; remembers collapse state.
- **Command palette (⌘K)** — fuzzy across areas/actions/automations/workflows/settings; "run this"
  verbs; recents + suggested.
- **Sheet / Modal / Drawer** — radius 2xl, focus-trapped, ESC + backdrop close, `inert` background,
  return-focus on close, mobile drag handle.
- **Run/Status badge** — the protected-status primitive: color + icon + label; sizes inline/chip.
- **Toast / inline status** — non-blocking, `role=status`, pause-on-hover; **undo toasts** for
  reversible actions instead of confirm dialogs; confirm dialogs reserved for irreversible/blast.
- **Empty states** — every surface ships a calm empty state + one primary action + a
  "set this up for me" shortcut to kill blank-page paralysis.
- **Progress / streak / success-rate** — forgiving language; ring/segment; celebratory micro-motion
  gated to non-reduced-motion + playful-leaning themes only.
- **Data table** — dense option (compact density), sticky header, keyboard row nav, column
  show/hide, sort, virtualized for thousands of rows (catalog/library/runs).
- **Canvas node** — schema-driven (see canvas spec); status ring uses protected `--run-*`; handles
  rendered from declared outputs.

## 9. Accessibility baseline (enforced in CI)

- **WCAG 2.2 AA** baseline across all themes/areas/modes; **AAA** available via the High-Contrast
  theme + text-scale. Automated axe + contrast checks gate merges.
- Every interactive element ≥ 44×44px hit area; visible `:focus-visible` ring (never bare
  `outline:none`); skip-links per view; full keyboard reachability with a documented key-map.
- `prefers-reduced-motion`, `prefers-contrast`, and forced-colors respected at the top a11y layer.
- Screen-reader semantics: landmarks, live regions for run/log streams (`aria-live="polite"`),
  labelled controls, status announced as text not color.
- Dyslexia font + adjustable text-scale (90–140%) without layout breakage (the locked layout +
  relative units guarantee this).

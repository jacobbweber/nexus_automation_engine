# Theming — Mode Engine, Area Overrides, Themes, Theme Studio

How dark/light, per-area retinting, and full themes resolve over the one token contract, plus the
10 built-in themes and the pipeline that lets an operator generate and apply their own.

## 1. Mode engine

- Default = `prefers-color-scheme`, persisted to local settings (survives container restart).
- Control is tri-state **System / Light / Dark**, plus **Auto-sundown** (manual schedule or a local
  sunrise/sunset table — no network call, honoring local-only).
- **Per-area mode override** is allowed ("Console always dark for NOC; Catalog follows system"),
  stored as a `{area: modeOverride}` map.
- Mode swap cross-fades `color`/`background` over 240ms; under reduced-motion it is instant (no
  disorienting flash).

## 2. Area-context overrides (bounded retint)

Each Nexus surface declares an **accent identity** and an **ambient tint** (used at 4–8% alpha).
Switching areas retints chrome (active nav, focus rings, primary buttons, progress) — never the
layout. Accents are chosen to never collide with protected status colors.

| Area | Accent identity | Feeling |
|---|---|---|
| **Dashboard** | signal blue | calm overview |
| **Catalog** | indigo | discovery |
| **Canvas** | teal | composition / build |
| **Library** | sage green | saved & governed |
| **Console** | amber | live execution |
| **Incidents** | coral (provably ≠ `--run-failed`) | attention, not alarm |
| **Governance** | violet | control & review |
| **Admin** | graphite + signal-cyan | system & access |

Override surface is intentionally tiny: `--area-accent`, `--area-accent-hover`,
`--area-accent-contrast`, `--area-tint`. Everything else inherits the theme.

## 3. The 10 built-in themes

Operator-appropriate spread: neutral/broad, minimalist, dark, dense-professional, two
ADHD/ADD-optimized, max-accessibility, a "fun-but-appropriate" terminal look, a war-room/projector
theme, and a long-session warm theme. All pass the validator's contrast + status-distinguishability
gates by construction.

1. **Signal** *(default — neutral)* — warm off-white `#FBF7F2` / warm charcoal `#221E1A`,
   confident signal-blue accent. The calm, trustworthy default.
2. **Paper** *(minimalist light)* — near-monochrome warm cream/ink, single restrained accent, serif
   reading surfaces, near-sharp radius, generous whitespace, reduced motion. For specs/README/logs
   reading.
3. **Midnight Ops** *(dark-first)* — low-glare deep slate, soft accents tuned for hours-long NOC
   sessions; status colors boosted for at-a-glance triage.
4. **Slate Pro** *(dense enterprise)* — cool graphite, restrained accent, compact density option,
   sharp-ish radius, dense tables. For power users and System dashboards.
5. **Focus Flow** *(ADHD/ADD — spotlight)* — muted field so nothing competes; **one** saturated
   accent reserved for the current task/run/CTA; inactive panels auto-dim; optional "task tunnel"
   recedes everything but the active card. Motion minimal, decorative animation off.
6. **Calm Clarity** *(ADHD/ADD — low-arousal)* — low surface-to-surface contrast but strong text
   contrast; muted earth palette; **no red except true danger**; large radii, extra spacing,
   motion off by default. Pairs with "one-thing-at-a-time" run mode.
7. **High Contrast (AAA)** *(max accessibility)* — ≥7:1 everywhere, 2px borders instead of shadows,
   no tints, forced-colors compatible, 3px focus rings. Auto-pairs with dyslexia font + reduced
   motion; doubles as the `prefers-contrast: more` fallback.
8. **Terminal** *(fun-but-appropriate)* — green/amber-on-near-black, mono display headers, subtle
   scanline texture (decorative layer, disabled under reduced-motion/contrast). Accents tuned to AA.
   For console-loving operators.
9. **Daylight** *(war-room / projector)* — high-clarity bright palette with boosted contrast and
   larger default text, tuned for well-lit ops floors, shared screens, and projectors.
10. **Ember** *(long-session warm)* — warm low-blue palette easy on the eyes for extended incident
    bridges and change windows; gentle accents, soft radius.

Each theme is authored as a `nexus-theme/v1` document (below) and snapshot-tested across
mode × area.

## 4. Theme contract (`nexus-theme/v1`)

```json
{
  "$schema": "nexus-theme/v1",
  "id": "ember",
  "name": "Ember",
  "author": "builtin",
  "version": "1.0.0",
  "base": "dark",
  "personality": { "radius": "soft", "density": "comfortable", "motion": "reduced" },
  "tokens": {
    "light": { "--bg": "#…", "--surface": "#…", "--text": "#…", "--accent": "#…",
               "--run-running":"#…","--run-ok":"#…","--run-warn":"#…","--run-failed":"#…","--run-skipped":"#…",
               "--success":"#…","--warn":"#…","--danger":"#…","--info":"#…","--focus":"#…" },
    "dark":  { "…": "…" }
  },
  "areas": { "canvas": { "--area-accent": "#…" }, "console": { "--area-accent": "#…" } },
  "a11y": { "minContrastBody": 4.5, "minContrastLarge": 3.0, "respectsForcedColors": true },
  "restrictions": { "layout": "locked", "spacingScale": "locked", "allowedKeys": "semantic-only" }
}
```

A theme supplies values **only** for an allow-listed semantic key set. No selectors, no CSS, no
layout, no spacing scale, no font *files* (fonts chosen by name from a vetted local list).

## 5. Theme Studio pipeline

Nexus ships a **deterministic Theme Studio** — a form + color pickers + live preview + validator.
There is **no AI/LLM** anywhere in this pipeline (or the system); the deterministic validator is
the sole gate, so a theme is *safe by construction*.

```
form / color pickers ─▶ candidate nexus-theme JSON
        ▼
 VALIDATE (deterministic gate):
   • JSON-schema conformance
   • key allow-list (reject any layout/spacing/selector/CSS attempt)
   • completeness (all required semantic keys for both modes)
   • CONTRAST engine: WCAG/APCA on every text-on-surface & accent-on-surface pair; auto-nudge
     lightness to pass or flag the failing pairs
   • PROTECTED STATUS check: running/ok/warn/failed/skipped mutually distinguishable +
     colorblind-safe + area-accents not colliding with status
   • forced-colors + reduced-motion compatibility
        ▼
 PREVIEW: live "kitchen-sink" board (buttons, cards, nav, run badges, log stream, table, canvas
   node, chart) under the candidate; side-by-side diff; "try across areas" toggle
        ▼
 APPLY/SAVE: write validated JSON to the themes volume; hot-reload via watcher; added to the
   user's library; previous theme kept as a revertible snapshot
```

The worst case for an invalid hand-authored theme is a validator rejection with the failing pairs
listed — never a broken layout or an inaccessible/illegible-status theme.

## 6. Docker volume strategy

```yaml
volumes:
  nexus_themes:         # user/studio-authored themes (writable)
  nexus_theme_presets:  # the 10 built-ins (read-only, shipped)
services:
  frontend:
    volumes:
      - nexus_theme_presets:/app/themes/presets:ro
      - nexus_themes:/app/data/themes:rw
  # validator runs server-side (not in the browser); the frontend only ever receives
  # already-validated theme JSON via GET /api/v1/themes
```

- Validation runs **server-side**; the frontend never receives an unvalidated theme.
- A file-watcher on `nexus_themes` emits an SSE `theme:changed` → the frontend hot-swaps without a
  reload.
- Themes are namespaced per user/profile; export/import is a single portable JSON file (no lock-in),
  consistent with the platform's local-first, no-secrets posture.

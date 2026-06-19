# Experience Roadmap — Ordered Implementation

The build order for the experience architecture, organized so each step unblocks the next. This is
the source the GitHub issues are generated from. Milestones continue the existing line
(3.0 ended at M18; M19 delivered canvas depth + the workflow library).

Labels follow the repo scheme: `type:feat|chore|test|docs`, `area:design-system|theming|a11y|
frontend|canvas|catalog|console|incidents|governance|admin|platform|ai`.

## Critical path

`A (foundation) → B (theme system) → C (shell)` then the surface-depth epics
`D…K` largely in parallel, finishing with `L (hardening)`. Epic A blocks everything.

---

### EPIC A — Design-system foundation *(M20; blocks all)*
1. **Token architecture & `@layer` cascade** — primitives→semantic layers; `data-mode/area/theme/density` attributes. `[area:design-system]`
2. **Semantic color contract + base ramps** — full contract incl. protected `--run-*`/status keys; Signal light+dark reference. *(dep 1)*
3. **Spacing/radius/type/elevation/motion scales** — exact values from `01_design_system.md`, as CSS vars **and** generated TS constants. *(dep 1)*
4. **Mode engine** — System/Light/Dark + Auto-sundown + per-area override + persistence + transition. `[area:theming]` *(dep 2)*
5. **Density + a11y top layer** — reduced-motion, prefers-contrast, forced-colors, dyslexia font, text-scale; a11y layer wins. `[area:a11y]` *(dep 3)*
6. **Component refactor to tokens** — Button, Input/Select/Textarea, Card, Modal/Sheet/Drawer, Toast, Tabs, Table, Empty-state, Progress, **Run/Status badge**. `[area:frontend]` *(dep 2,3)*
7. **A11y + contrast CI harness** — axe + contrast + 44px/focus lint in CI. `[area:a11y][type:test]` *(dep 6)*

### EPIC B — Theme system & Theme Studio *(M21)*
8. **Area-context override layer** — accent/tint/persona retint on area switch; collision check vs status. `[area:theming]` *(dep 4,6)*
9. **`nexus-theme/v1` schema + TS types + deterministic validator** — schema, key allow-list, completeness. `[area:theming]` *(dep 2)*
10. **Contrast/APCA + protected-status validation engine** — WCAG/APCA pass, status distinguishability, colorblind sim, auto-nudge. `[area:a11y][area:theming]` *(dep 9)*
11. **Ship the 10 built-in themes** — author + snapshot-test each across mode×area. `[area:theming]` *(dep 8,10)*
12. **Theme volume + server-side validation + hot-reload** — Docker volumes, `GET /api/v1/themes`, SSE `theme:changed`. `[area:platform][area:theming]` *(dep 9)*
13. **Theme Studio: deterministic form + live kitchen-sink preview + diff** — `[area:theming]` *(dep 11)*
14. **Theme import/export + theme library UI** (Platform/System). `[area:theming]` *(dep 12)*
15. **Optional local-model theme assist (adapter, off by default)** — `[area:ai][area:theming]` *(dep 10,13)*

### EPIC C — Shell & cross-cutting primitives *(M21)*
16. **App shell + area navigation rail** (collapsible, retinting, keyboard). `[area:frontend]` *(dep 8)*
17. **Command palette (⌘K) + global search** ("find-and-run anything"). `[area:frontend]` *(dep 16)*
18. **Notifications feed** (run finished / approval requested / incident opened). `[area:frontend]` *(dep 16)*
19. **Empty-state + "set this up for me" pattern** + offline/degraded states. `[area:frontend]` *(dep 6)*

### EPIC D — Dashboard depth *(M22)*
20. **Fleet pulse + trends (success-rate/MTTR) + change-window peek.** `[area:frontend]` *(dep 16)*
21. **"Needs attention" feed + my-queue/recents/favorites + live activity stream.** `[area:frontend]` *(dep 17)*

### EPIC E — Catalog depth *(M22)*
22. **Faceted discovery + collections + favorites/recents + popularity/success-rate.** `[area:catalog]` *(dep 16)*
23. **Automation detail (docs/params/risk/owner/last-runs) + comparison.** `[area:catalog]` *(dep 22)*
24. **Logic-Flow tab (animated DAG + live trace).** `[area:catalog]` *(dep 23)*
25. **Blast-radius preview + run-from-template wizard + parameter presets/saved targets (CMDB pickers, dry-run-first).** `[area:catalog]` *(dep 23)*

### EPIC F — Canvas depth *(M22)*
26. **Comprehension aids: minimap, auto-layout, fit/search, group/comment nodes.** `[area:canvas]` *(dep 16)*
27. **Graph lint/validation (cycle/unreachable/missing-params/type) inline.** `[area:canvas]`
28. **Dry-run/plan preview + blast-radius overlay.** `[area:canvas]` *(dep 25)*
29. **Live run overlay (per-node status + log tail + timing).** `[area:canvas][area:console]`
30. **Run replay / time-travel + version visual diff.** `[area:canvas]` *(dep 29)*
31. **Subgraph templates / reusable blocks.** `[area:canvas]`

### EPIC G — Library depth *(M22)*
32. **Per-workflow drill-down (run history, success-rate, MTTR, schedule/incident links).** `[area:frontend]` *(dep 21)*
33. **Lifecycle quick-actions + bulk operations (tag/own/archive/schedule).** `[area:frontend]`

### EPIC H — Console depth *(M22)*
34. **Live job stream (ANSI, pin, aria-live) + in-run log search/filter + artifacts.** `[area:console]` *(dep 6)*
35. **Run compare + controls (retry/cancel/re-run/resume) + step timeline.** `[area:console]` *(dep 34)*

### EPIC I — Incidents depth *(M23)*
36. **RCA assist: similar-past-failures + suggested remediations + failure-mode tagging.** `[area:incidents]`
37. **Trends: top failing automations + MTTR by domain + recurring-failure detection.** `[area:incidents]`

### EPIC J — Governance & Admin depth *(M23)*
38. **Approvals inbox + review history audit.** `[area:governance]`
39. **Change calendar (CHG + schedules + windows) + conflict detection.** `[area:governance]`
40. **Validation policy editor + pruning/review dashboard.** `[area:governance]`
41. **RBAC matrix editor + users/entitlements + capability registry.** `[area:admin]`

### EPIC K — Platform / System depth *(M23)*
42. **Connector registry + simulation controls + per-connector health.** `[area:platform]`
43. **Resource/container view + local-only status banner + logs/restart.** `[area:platform]`
44. **Accessibility center (mode/theme/density/motion/font/contrast/scale + guided setup).** `[area:a11y][area:platform]` *(dep 5,14)*
45. **Backup/export (portable JSON) + notifications/rules config.** `[area:platform]`

### EPIC L — Hardening & polish *(M23)*
46. **Theme × area × mode × density visual-regression matrix.** `[type:test][area:theming]`
47. **Keyboard-only + screen-reader pass per surface; AAA spot-checks.** `[area:a11y][type:test]`
48. **Optional Assistant: explain-failure / suggest-remediation / draft-CHG / describe→scaffold (local-model adapter, off by default).** `[area:ai]` *(dep 15)*

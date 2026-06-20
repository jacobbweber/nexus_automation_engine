# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses Semantic Versioning.

## [Unreleased]

### Added
- **M28.1 — canonical config serializer** (v4.0 Pillar E): a deterministic snapshot of every config
  artifact (workflows, CMDB schemas + lineage, pinning rules, catalog templates, validation policy,
  schedules, change templates) → stable file paths + key-ordered JSON with volatile audit timestamps
  stripped, so re-serializing unchanged config is **byte-identical**. The basis for committing config
  to Git (history/diff/restore) without spurious diffs.
- **M27.5/27.6 — Guardrails management page + ADR-0012** (v4.0 Pillar D): a **Determinism &
  Guardrails** page (`/determinism`, nav + palette) where admins author pinning rules with a
  schema-driven selector builder (CI type from the CMDB registry + tag/field predicates), a workflow
  picker, and trigger/enforcement selectors — and everyone sees **coverage** per rule (CIs
  guaranteed, compliant vs drifted, missing-workflow warnings). Answers "what is guaranteed about my
  estate, and where does reality differ?" Adds the `Determinism` API client. ADR-0012 records the
  pinning/reconcile decision. Completes M27.
- **M27.4 — pinning API + CI-change trigger** (v4.0 Pillar D): REST for pinning rules
  (`GET /determinism/rules[/{id}]`, admin `PUT`/`DELETE`), `GET /determinism/coverage`, and admin
  `POST /determinism/reconcile`. The CI-change path (M26.5) now also fires the **on-change trigger**:
  enforce-mode rules whose guaranteed workflow resolves open a review approval automatically.
- **M27.2/27.3 — pinning reconciler + coverage** (v4.0 Pillar D): a deterministic reconciler turns
  rules + live CMDB CIs into a **pinned-actions plan** (per CI × matching rule, with the enforcement
  mode: assert / enforce / gate), optionally filtered by trigger; and a **coverage** computation
  answers *"what is guaranteed about the estate, and where does reality not match?"* — per rule:
  matched CIs, workflow-exists, and (for assert rules) compliant/drifted via M25. `DeterminismService`
  runs both over the live CMDB.
- **M27.1 — workflow pinning rules** (v4.0 Pillar D): a new `determinism` context — a `PinningRule`
  binds a **selector** (CI type + tag/field predicates) to a **guaranteed workflow**, a **trigger**
  (create/change/schedule/on-demand), and an **enforcement mode** (assert | enforce | gate), with a
  pure priority-ordered matcher. Seeded example rules (every VM → tag/CMDB validation; DR-Tier-0 VM →
  guaranteed Zerto DR VPG) and tagged a seeded VM `DR-Tier=0` so the rule demonstrates. Management-
  by-invariant: declare what must be true of the estate.
- **M26.6/26.7 — review UI + ADR-0011** (v4.0 Pillar C): a **Review Packet viewer** with a
  **Technical / Non-technical / Executive** audience toggle + flowchart (executive view hides
  connectors/params, shows plain outcomes + risk + rollback), an **Approvals queue** (`/approvals`,
  in nav + palette) to approve / reject / request-changes pending run & CI-change reviews, and the
  `Review` API client. ADR-0011 records the multi-audience-review + run-approval decision. Completes
  M26 — humans of every technical level can now review and gate changes. (A distinct executive RBAC
  role is a deferred security-model change; the executive *view* ships now.)
- **M26.5 — CI-change approval path** (v4.0 Pillar C): proposing a CI add/modify
  (`POST /review/ci-change`) runs the CMDB health check (M24) and opens an approval request
  (`source_type=ci_change`) carrying the health score + remediation hints — so a human approves the
  change, gated on its health, before it applies.
- **M26.4 — run-level approval gate** (v4.0 Pillar C): a workflow run that the review policy says
  needs approval is now **blocked until a human approves**. `ApprovalRequest` (with a packet
  snapshot) is persisted; `request_approval` opens a pending request (de-duped), `decide`
  approves/rejects/requests-changes. `start_run` enforces the gate (plan/compliance runs are exempt,
  being read-only). API: `GET /review/approvals` (queue), `GET /review/approvals/{id}`,
  `POST /review/approvals`, `POST /review/approvals/{id}/decision`.
- **M26.3 — multi-audience Review Packet builder** (v4.0 Pillar C): a deterministic builder that
  renders exactly what a run will do for three audiences — **technical** (per-step connector/action/
  resolved params + idempotency), **non-technical/executive** (a plain-English narrative composed
  from each block's authored plain summary, in execution order, with overall risk/outcome/rollback),
  and a **flowchart** phase list — plus the change-classification headline. `GET /review/packet/{id}`
  builds it for a workflow. No AI — composition only.
- **M26.2 — change classification engine** (v4.0 Pillar C): a new `review` context with a pure,
  deterministic classifier — `standard | normal | emergency` from risk + blast radius + target
  environment (prod) + idempotency class — and a tunable `ReviewPolicy` mapping each class to a
  required reviewer level (none / team-lead / executive), with escalation to executive on
  high/critical risk or large blast radius. `assess()` also returns the human reasons.
- **M26.1 — plain-language building-block summaries** (v4.0 Pillar C): every catalog building block
  now carries a `plain_summary` (`input → action → outcome` + rollback) — authored once, composed
  later into multi-audience review packets. Seeded deterministically across the catalog from each
  block's metadata, persisted, and shown as an "In plain language" block on the catalog detail.
- **M25.5 — compliance posture dashboard + drift viewer** (v4.0 Pillar B): a **Compliance** surface
  (`/compliance`, in the nav rail + command palette) showing % compliant, evaluated/drifted counts,
  top-drifted, a drift trend sparkline from snapshot history, and an admin "Run sweep now". A shared
  `DriftReportView` (desired-vs-observed per field + reconcile action) + `ComplianceBadge`, reused on
  the catalog detail via a **"Check compliance"** action. Adds the `Compliance` API client. Completes
  M25 — the platform now continuously *asserts desired state* and shows the gap.
- **M25.4 — scheduled compliance sweeps → posture + incidents** (v4.0 Pillar B): a new `compliance`
  context that evaluates every published workflow in compliance mode, snapshots the estate's
  **posture** (evaluated / compliant / drifted / total drift / top-drifted), and **opens incidents**
  for drifted workflows (de-duped per open source). Runs on the scheduler cadence (every N ticks via
  the M11 loop) and on demand (`POST /compliance/sweep`, admin); `GET /compliance/posture[/history]`
  expose snapshots. Drift is now a continuously-managed signal, not a surprise.
- **M25.3 — compliance-mode runs** (v4.0 Pillar B): run any building block or workflow in
  *compliance mode* — a read-only evaluation that returns a `DriftReport` without mutating.
  `POST /catalog/templates/{id}/compliance` evaluates one block; `POST /canvas/workflows/{id}/
  compliance` evaluates every automation task and **aggregates** the drift across the workflow.
  Deterministic + auth-gated. (The drift/posture UI lands in 25.5.)
- **M25.2 — drift / compliance model** (v4.0 Pillar B, ADR-0010): a first-class `DriftReport`
  (per-resource + per-field desired-vs-observed: `compliant | drifted | unknown`, with the reconcile
  action that would converge each, an aggregate status + drift count) and a `CompliancePort`
  (`evaluate_compliance`). A deterministic simulated evaluator produces believable, *stable* drift
  per request (seeded by target+action; check-only actions are inherently compliant) plus an
  aggregation helper for rolling up across a workflow's steps. Never mutates.
- **M25.1 — idempotency-class contract** (v4.0 Pillar B, ADR-0010): every connector action and
  catalog building block now declares an `IdempotencyClass` (`idempotent | check_only |
  non_idempotent`) — a shared-kernel primitive. Connector actions auto-classify from their name
  (destructive verbs → non-idempotent, read/plan → check-only) with explicit override; templates are
  seeded via the same inference; the catalog detail shows an idempotency chip. Makes "all automation
  is idempotent" an enforceable contract, not a hope. Also aligned template `ci_type` defaults to the
  standardized `vm` vocabulary.
- **M24.7 — CI health badges + Lineage Explorer** (v4.0 Pillar A): a reusable `HealthBadge`
  (status + score, colour + text) and a **CMDB Lineage Explorer** (`/cmdb-explorer`) — look up any CI
  to see its deterministic health (badge/score), its required relationships with **gaps highlighted**
  (satisfied vs missing), and field/tag/lineage issues + remediation hints. Linked from the command
  palette and a new **CMDB governance** card on Admin (also links Schema Studio). Completes M24.
- **M24.6 — CMDB Schema Studio** (v4.0 Pillar A): an admin surface (`/cmdb-schema`, linked from the
  command palette) to define/edit CI type **schemas** (fields with datatype/required/enum/regex,
  required tags, naming pattern) and **lineage** (typed required relationships), saved through the
  deterministic backend validator — author→validate→save, mirroring Theme Studio. Adds the `Cmdb`
  API client (schemas/lineage/validate-ci/ci-health) + types.
- **M24.5 — lifecycle gate consults CMDB health** (v4.0 Pillar A): the execution lifecycle-validation
  gate now optionally requires the target CI to be healthy against its schema + lineage. Two new
  `ValidationPolicy` flags (`require_healthy_ci`, `min_health_score`, default off) — when enabled, a
  run targeting a degraded/unhealthy CI is rejected with the top issues; missing-schema CI types are
  skipped (can't assess). Off by default, so existing behavior is unchanged.
- **M24.4 — CMDB API + standardized CMDB data** (v4.0 Pillar A): REST surface for the `cmdb`
  context — `GET /cmdb/schemas[/{type}]` + admin `PUT`, `GET /cmdb/lineage[/{type}]` + admin `PUT`,
  `POST /cmdb/validate-ci` (ad-hoc record → health report), and `GET /cmdb/ci/{name}/health`
  (resolves the CI via the ServiceNow ACL connector and runs the checker). The simulated CMDB was
  enriched to the **standardized CI vocabulary** (vm/host/cluster/datastore/volume/backup_policy)
  with tags + typed relationships, so health checks have real signal end-to-end (web-prod-01 reads
  healthy; app-stg-01 reads degraded).
- **M24.3 — CMDB health checker** (v4.0 Pillar A): the deterministic payoff of the `cmdb` context —
  `check_ci(record, schema, lineage)` → a **CI Health Report** (field/lineage/tag issues with
  severity, a stable explainable **health score**, status healthy/degraded/unhealthy, and
  remediation hints). Detects missing/invalid fields, naming violations, missing/orphaned/
  cardinality-wrong relationships, and missing required tags. `CmdbHealthService` resolves a CI's
  schema + lineage and runs it. Pure, no AI — the basis for the lifecycle gate, pickers, and pinning.
- **M24.2 — CMDB lineage specs** (v4.0 Pillar A): per CI type, the typed required relationships
  (target type, direction up/down, cardinality, required) that make a CI "whole" — with a
  deterministic validator (unknown-target + duplicate-name checks) and a **required-dependency cycle
  detector** across the whole set. Seeded a consistent DAG (application→vm→{host→cluster,
  datastore→volume→backup_policy}). Consumed next by the health checker (24.3).
- **M24.1 — CMDB CI type schema registry** (v4.0 Pillar A, ADR-0009): a new `cmdb` bounded context
  that defines CIs as a contract — schema-as-data per CI type (fields with datatype/required/enum/
  regex/sensitivity, required tags, naming pattern), a deterministic schema validator, a versioned
  registry (list/get/upsert), and seeded schemas for vm/host/cluster/datastore/volume/backup_policy/
  application. Foundation for lineage, the health checker, deterministic pinning, and review impact.

### Changed
- **CMDB CI type vocabulary**: the simulated ServiceNow CMDB now uses `vm` (was `server`) and adds
  host/cluster/volume/backup_policy CIs with tags + relationships (lifecycle-validation tests updated
  accordingly) — resolving the v4.0 open question and aligning the CMDB with the seeded schemas.

### Fixed
- **Run-status colour distinguishability** (QA): dark `--run-skipped` was a warm taupe that sat too
  close in hue to amber `--run-warn` (the theme validator's distinguishability check flagged it
  across 8 built-ins), and Terminal's `--run-running` was the same green as `--run-ok`. Skipped is
  now a desaturated cool gray and Terminal's running is a classic-terminal cyan, so all 10 built-ins
  validate with zero warnings — locked in by a new test asserting `validateTheme` is warning-free.
- **Light mode stuck dark** (QA): selecting Light (or any light-resolving mode) left the app dark.
  `index.html` ships `<html class="dark">` for anti-FOUC, and the mode engine updated `data-mode`
  but never cleared that legacy class, so the `:where(.dark)` token rule pinned every surface to
  dark. The mode engine now keeps `.dark` in sync with the resolved mode. Regression-tested.
- **SPA deep-link 404** (QA): when the API serves the built frontend (single-container deploy),
  a hard refresh or deep link to a client-side route (e.g. `/catalog`, `/canvas`) returned
  `{"detail":"Not Found"}` instead of the app. The static mount now falls back to `index.html`
  for unknown non-API paths (unknown `/api/*` paths still return JSON 404s; real assets are
  served verbatim).

### Added
- **Seeded incident triage board** (QA): startup now opens incidents for a sample of the seeded
  failed jobs, spread across the board columns (NEW/TRIAGE/INVESTIGATING/RESOLVED) with severities,
  assignees, and resolution times — so the Incidents board, mean-time-to-resolution, top-failing-
  automation trends, and RCA failure-mode tags all have realistic data in simulation mode instead
  of an empty board next to 13 failed runs. Idempotent; pure-ish `seed_incidents` unit-tested.
- **M23 — hardening: token regression + a11y tests** (L46/L47, #107/#108): a **theme-token
  regression matrix** snapshots every built-in theme's generated CSS (light + dark) so unintended
  palette changes fail CI, and an **automated structural a11y suite** asserts key components expose
  correct roles + accessible names (color contrast already gated by A7). Full browser/screen-reader
  audit remains the documented manual step. **This completes the M20–M23 experience roadmap.**
- **M23 — RBAC matrix viewer** (J41, #102): a `GET /auth/rbac-matrix` endpoint exposes the role ×
  capability baseline; Admin renders it as a grid. Read-only by design — the baseline is part of the
  security model (refined per-resource by entitlements), not a runtime toggle. (Users list endpoint
  also surfaced.)
- **M23 — backup / export** (K45, #106): an admin-only `GET /platform/export` returns a portable
  JSON bundle (`nexus-export/v1`) of workflows + themes + schedules (no secrets), downloadable from
  Admin. (Restore/import is a deferred follow-up — it needs careful conflict handling.)
- **M23 — platform status** (K43, #104): a `GET /platform/status` endpoint (uptime, DB
  reachability, workflow/job counts, scheduler + simulation state, version/env) surfaced as a
  **Platform status** card in Admin. (Real container/orchestration metrics remain a deploy-time
  follow-up — local/simulation runs a single in-process app.)
- **M22 — run retry** (H35, #96): one-click **retry** on a run (re-runs the workflow with the
  original inputs via `POST /canvas/runs/{id}/retry`) from the Library run history — completes H35
  with the per-step timeline. (Side-by-side run compare + cooperative cancel noted as enhancements.)
- **M22 — dry-run / plan** (F28, #89): a **Dry run** action on the canvas (and a `plan` flag on
  `POST /canvas/workflows/{id}/run`) executes the whole DAG with every automation task forced into
  **check mode** so nothing mutates — a safe plan of the workflow. Pure `_apply_plan` unit-tested.
- **M22 — blast-radius preview** (E25, #86): a `POST /connectors/servicenow/impact` endpoint
  computes which CMDB CIs an action on a target would touch (the target + **cluster siblings**);
  the canvas surfaces it on automation-task / CMDB-lookup nodes that target a literal CI, so an
  operator sees the impact before running. (Run-from-template wizard + saved presets remain follow-
  ups.)
- **M23 — incident RCA assist** (I36, #97): each incident card shows a **failure-mode tag**
  (timeout/permission/connection/validation/approval/capacity, from keywords), a **similar-past-
  failures** count (same title), and a **"remediation available"** hint when a similar incident
  already has a remediation workflow — all from data + rules, no AI. Pure helpers unit-tested.
- **M22 — canvas subgraph blocks** (F31, #92): save the current graph as a named, reusable **block**
  (persisted locally) and insert clones of it (fresh node ids, remapped edges, offset position) from
  a Blocks section in the palette. Pure `cloneBlock` is unit-tested.
- **M22 — canvas run replay** (F30, #91): a completed run's recorded step trace can be replayed onto
  the graph — `/canvas?id=<wf>&replay=<run>` (or the ▶ replay link in the Library run history)
  animates each node's status in step order (instant under reduced-motion), with a replay banner
  (↻ again / exit). Live per-node status overlay during a run (F29) was already in place.
- **M23 — incident trends** (I37, #98): the Incidents board gains a trends row — open/resolved
  counts, **mean time to resolution**, and **top failing automations** — all computed client-side
  from the board data (pure `incidentTrends`, unit-tested).
- **M23 — connector registry view** (K42, #103): the Admin page's connector cards now show a
  simulation/health indicator (from `/health`) and expand to list each connector's **actions**
  (label, name, param count) alongside capability chips (check-mode / diff / streams-logs).
- **M23 — validation policy editor** (J40, #101): admins can edit the single lifecycle
  `ValidationPolicy` (CMDB-consistency, reject-retired, reject-unknown-CI, block-destructive-on-
  cluster, max review age) in Governance via the existing admin-only `PUT /policy` — the one gate
  every execution consults (ADR-0006). (The pruning/review-status dashboard half shipped in M18.)
- **M22 — run step timeline** (H35 partial, #96): run-history rows (in the Library drill-down)
  expand to a **per-step timeline** — each step's status, node, type, retry count, and duration —
  fetched on demand from `/canvas/runs/{id}`. (Run compare + retry/cancel controls deferred — they
  need new backend mutation endpoints.)
- **M22 — Library lifecycle quick-action** (G33, #94): the per-workflow drill-down drawer can
  **submit a draft workflow for review** in one click (then refreshes the library). (Bulk
  tag/own/archive operations deferred — they need new backend endpoints.)
- **M22 — Console log search + download** (H34, #95): the Execution Console (already live-streaming
  with ANSI handling) gains an in-run **filter** (with match count, auto-scroll paused while
  filtering), a **download log** action, and an `aria-live` log region for screen readers.
- **M23 — Accessibility Center** (K44, #105): a dedicated `/accessibility` page consolidating color
  mode + **auto-sundown schedule** + **per-area mode overrides** (e.g. keep the Console dark),
  density, dyslexia font, text-scale, and theme — surfacing the sundown/per-area controls the mode
  engine already supported but had no UI for. Linked from the shell.
- **M23 — change calendar from ServiceNow CMDB** (J39, #100): the Governance page gains a change
  calendar — **CHG records are pulled from the (simulated) ServiceNow CMDB connector** as the system
  of record (`GET /connectors/servicenow/changes`), shown as a day-grouped agenda with window
  times, state, assignment group, and affected CIs, plus **conflict detection** (changes whose
  windows overlap on a shared CI are flagged). Pure `detectConflicts` is unit-tested.
- **M22 — Library per-workflow drill-down** (G32, #93): a details drawer in the Workflow Library
  shows a workflow's usage summary (runs / success / failures) and **recent run history** (status,
  start, duration) via `/canvas/workflows/{id}/runs`, with quick links to the canvas and console.
- **M22 — Canvas comprehension aids** (F26, #87): fit-to-view, zoom in/out/reset controls, and a
  node search that centers + selects a node by name — overlaid on the canvas. (Minimap / auto-layout
  / group-comment nodes remain as follow-ups under the same issue.)
- **M22 — Canvas graph lint** (F27, #88): an inline pre-run linter surfaces structural problems
  (missing Start/End, dangling edges, unreachable nodes, cycles, and missing required parameters
  per the node schema) in a strip under the canvas toolbar; clicking an issue selects the offending
  node. Pure `lintGraph` is unit-tested.
- **M22 — Catalog comparison** (E23, #84): select 2–3 automations and compare them side-by-side
  (vendor, domain, risk, type, duration, version, check/diff support, tags, prerequisites) via a
  compare tray + modal. (Faceted discovery E22 #83 and the Logic-Flow tab E24 #85 were already
  delivered by the M14 catalog-at-scale work.)
- **M22 — Dashboard needs-attention + favorites** (D21, #82): a **Needs attention** card
  aggregating workflows awaiting review, failed runs, and stale / never-reviewed automations (each
  drill-through, hidden when zero with an "all clear" state), and a **Favorites** card of starred
  workflows. Adds a shared `useFavorites` hook (localStorage, cross-component sync) and a **star
  toggle** in the Workflow Library. Pure `toggleId` unit-tested.
- **M22 — Dashboard fleet pulse** (D20, #81): the Operations Dashboard now shows a
  drill-through pulse (running / succeeded / failed → console/incidents), **trend cards**
  (success rate with color thresholds, average run duration, total/in-flight), a richer recent
  activity stream with timestamps, and an **upcoming-scheduled / change-window peek**. Pure
  `summarizeJobs` (case-insensitive counts, success rate, avg duration) is unit-tested.
- **M21 — empty states + offline/degraded banner** (C19, #80): a reusable calm `EmptyState`
  (icon + title + helper + action; adopted in the Library) and a non-blocking `ConnectionBanner`
  that watches the browser online state + pings API health and surfaces a clear "backend
  unreachable, retrying" notice that self-clears on recovery. **Completes the M21 shell (C16–C19)
  and the M21 theme/shell milestone.**
- **M21 — notifications feed** (C18, #79): a non-blocking bell in the shell that aggregates
  **open incidents, pending approvals, and recently finished runs** (derived from existing
  endpoints — no new backend), with an unread badge, mark-all-seen on open, and click-through to
  the relevant area. Pure `buildNotifications` mapping is unit-tested.
- **M21 — ⌘K command palette** (C17, #78): a global, keyboard-first "find-and-run anything"
  overlay (⌘K / Ctrl-K) that fuzzy-searches areas, saved workflows (deep-linking into the canvas),
  and quick actions, with recents and arrow/enter/esc navigation. Dependency-free fuzzy matcher
  (unit-tested) with start + contiguous-run bonuses.
- **M21 — collapsible, keyboard-navigable nav rail** (C16, #77): the app-shell rail collapses to
  an icon-only strip (persisted), with tooltips when collapsed, and supports arrow-key roving focus
  (Up/Down/Home/End) across nav items plus a proper `<nav aria-label>` landmark. Active-item +
  logo retint per area (from B8) carry through.
- **M21 — theme import/export + library management** (B14, #75): the Theme Studio gains a
  Library & portability panel — **export** the draft as portable JSON (no lock-in), **import** a
  theme file (client-validated, loaded into the editor to preview before saving), and a
  **custom-theme list** with delete (built-ins are read-only). The theme provider exposes `reload`
  for instant refresh after save/delete (in addition to SSE hot-reload). Completes the M21 theme
  system (B8–B14).
- **M21 — Theme Studio** (B13, #74): a fully deterministic theme-authoring page (`/theme-studio`,
  linked from the shell): start from any theme, edit tokens with color pickers (light/dark tabs),
  see **live validation** (the same `validateTheme` gate — contract + WCAG-AA) and a **live
  kitchen-sink preview** (buttons, run-status badges, card/links) under the candidate, an
  **auto-fix-contrast** helper (`nudgeForContrast`), and **save** to the server (re-validated, then
  it appears in the picker). No AI involved.
- **M21 — theme service: volume + server-side validation + hot-reload** (B12, #73): a backend
  `theming` platform module persists user/Studio themes to a writable directory (mounted as the
  `nexus_themes` Docker volume) and serves only themes that pass a **Python port of the
  deterministic validator** (allow-list + WCAG-AA, mirroring the frontend gate). `GET /themes`
  lists validated themes, `POST /themes` validates + saves (auth required; 422 on violation),
  `GET /themes/stream` is an SSE feed emitting `theme:changed` on volume changes. The frontend
  merges server themes into the picker and **hot-reloads** via the stream. No AI anywhere.
- **M21 — 10 built-in themes** (B11, #72): Signal, Paper, Midnight Ops, Slate Pro, Focus Flow +
  Calm Clarity (ADHD/ADD), High Contrast (AAA), Terminal, Daylight, Ember — each built from the
  validated base + overrides and **gated through `validateTheme` in CI** (every theme passes the
  AA/allow-list contract). Themes apply by injecting their tokens into the `@layer theme` cascade
  (`theme-apply.ts`) keyed by `data-theme` (dark override scoped); a `ThemesProvider` persists the
  choice and a `ThemePicker` (with swatches) lives in the shell's Display & accessibility panel.
- **M21 — theme schema + deterministic validator** (B9/B10, #70/#71): the `nexus-theme/v1` contract
  (`shared/theme/theme-schema.ts`) — a theme is **data** that may only remap an allow-listed set of
  semantic tokens for light + dark. `validateTheme()` is the sole safety gate (no AI): it checks
  shape, the **key allow-list** (rejecting any layout/spacing/CSS-injection attempt), completeness,
  valid hex colors, **WCAG-AA contrast** (text/bg, text/surface, muted/bg, accent-contrast/accent,
  run-status AA-large), and **protected-status hue distinguishability**, plus a `nudgeForContrast`
  auto-fix. Extends `contrast.ts` with hsl/hue-distance/hex helpers. Fully unit-tested.
- **M21 — area-context overrides** (B8, #69): each Nexus surface (Dashboard/Catalog/Canvas/Library/
  Console/Incidents/Governance/Admin) retints the chrome (active nav pill, primary buttons, focus
  rings, logo) via an `@layer area` over the token contract — light + dark variants, all WCAG-AA
  with their contrast text. Accents are hue-separated from the protected status colors (≥30°) so an
  accent can never be mistaken for run status; the active area is driven from the route and also
  feeds the mode engine's per-area override. Gated by an `area.test.ts` (AA + hue-distance).
- **M20 — contrast/a11y CI gate** (A7, #68): a reusable WCAG **contrast utility**
  (`shared/theme/contrast.ts` — luminance, ratio, AA/AAA helpers; reused later by the theme
  validator) plus a test that gates the **Signal default palette** (light + dark) at WCAG AA in CI.
  Building the gate surfaced and fixed real issues: the light accent was darkened so white button
  text clears AA, dark mode got a dark `--accent-contrast`, and the status badge now renders its
  label in `--text` with the color carried by the icon. **Completes the M20 foundation (A1–A7).**
- **M20 — component refactor + protected status badge** (A6, #67): the shared primitives
  (Page/Card/Button/StatusBadge) now consume the semantic token contract (radii/spacing/elevation
  vars; `Button` retints per area + gains soft/danger/quiet variants and 44px targets). A global
  `:focus-visible` ring covers every interactive element. `StatusBadge` is now the **protected
  Run/Status primitive** — each status is conveyed by an **icon (shape) plus color**, never
  color-alone, resolving through the `--run-*`/status tokens. Spinner stops under reduced-motion.
- **M20 — display & accessibility preferences** (A5, #66): a `PrefsProvider` drives the density
  (cozy/comfortable/compact), dyslexia-font, and text-scale (90–140%) layers via root
  data-attributes + root font-size; persisted; surfaced as a "Display & accessibility" disclosure
  in the app shell (reused later by the full Accessibility center). Pure logic unit-tested.
- **M20 — mode engine** (A4, #65): a `ModeProvider` applies the resolved light/dark to
  `<html data-mode>` with **System / Light / Dark**, **auto-sundown** (manual schedule, overnight
  wrap), **per-area override**, and `localStorage` persistence; OS-preference is followed in System
  mode; the dark/light swap cross-fades (instant under reduced-motion). A segmented `ModeToggle`
  lives in the app shell. Pure `resolveMode` logic is unit-tested.
- **M20 — token foundation** (experience architecture, ADR-0007): introduced the layered
  resolution cascade (`shared/theme/tokens.css` — `primitives → semantic → mode → area → theme →
  density → a11y`), the full **semantic token contract** (incl. protected `--run-*` status tokens),
  the Signal warm-neutral default palette with `data-mode` dark support, density + a11y
  (reduced-motion / dyslexia) layers, and a **TS constants mirror** (`shared/theme/tokens.ts`) for
  canvas/SVG. Existing components keep working via compatibility aliases. Closes A1–A3 (#62–#64).
- **M19 — run-inputs prompt**: launching a workflow whose Start node declares inputs now opens a
  prompt to supply those ad-hoc values (pre-filled with declared defaults) instead of always
  running with an empty payload; input-less workflows still run in one click.
- **M19 — workflow library, ownership metadata & usage reporting**: workflows now carry
  **owner / team / tags** (preserved across graph edits), and a new
  `GET /canvas/workflows/report` joins each workflow with its run telemetry (run count, success /
  failure, last run, success rate). A new **Workflow Library** page (`/library`) lists every saved
  workflow filterable by team/tag with usage and governance state, and opens one in the canvas via
  `/canvas?id=`. The canvas toolbar edits team/tags and shows the owner.
- **Seeded enterprise workflow library**: a fresh login is now a full control plane — ~14
  realistic, governed workflows across **Storage / Compute / Backup / ITSM / Security / Platform /
  Networking** (CMDB-driven inventory, approval gates, secret leasing, cluster-aware destructive
  guards, telemetry-driven self-healing, Terraform plan→apply), with varied review states
  (published / submitted / draft) and seeded run telemetry.
- **Additive SQLite column migration**: `init_db` now adds ORM columns missing from an existing
  SQLite table (additive-only) so a persisted dev DB picks up new fields without a manual reset.
- **M19 — schema-driven node parameters** (`node_specs.py`, `GET /canvas/node-types`): every
  canvas node type now publishes a typed parameter schema, so the property panel renders guided
  controls (select, toggle, number, key-value, multi-select, cases, assignments, run-inputs) from
  data instead of raw JSON. Adding a parameter is a one-line registry change — extensible per node.
- **Richer condition logic**: the Condition node gained operators `>=`, `<=`, `not_contains`,
  `starts_with`, `ends_with`, `matches_regex`, `in_list`, `is_not_empty`, plus a **case-sensitive**
  toggle, evaluated in the engine's `_compare`.
- **CMDB field picker** (`GET /connectors/servicenow/fields`): the CMDB-lookup node lets operators
  pick a CMDB table → choose real CI fields from a catalogue (narrowed per table) → use them
  conditionally downstream. The simulated CMDB exposes its table/field metadata.
- **Dynamic node output handles**: node branch handles (true/false, switch cases, error) are now
  rendered from each node's declared `outputs`, not hard-coded per type.

### Changed
- **Audit B1 — static typing**: adopted **mypy** in CI (clean across 125 files). Fixed real type
  issues found along the way and renamed shadowing `list()` repository/service methods to
  `list_all()`.
- **Audit Q2 — de-dup**: extracted the duplicated live-broadcast broker into a shared-kernel
  `AsyncBroker`; the execution and canvas brokers are now thin singletons over it.
- **Audit B2 — hardened gate**: enabled ruff **`S` (flake8-bandit) security rules** (with
  documented exceptions; the reviewed `eval` is annotated and the lone `assert` replaced by a
  guard), and added **test coverage** reporting to CI (91% at adoption).

### Fixed
- **Audit A1 — crash recovery**: a startup recovery sweep marks orphaned PENDING/RUNNING jobs and
  RUNNING workflow runs as FAILED after a restart, so persisted state stays honest. Documented the
  single-instance ceiling.

### Added
- **M18 CMDB Lifecycle Validation** ("origin-story validation", `lifecycle_validation` context,
  ADR-0006): every automation must carry required metadata (authored_by, approved/updated/reviewed
  dates, CI type + heritage) and pass a **CMDB CI-lifecycle consistency check** before it runs.
  Rejects runs whose target contradicts the CMDB — retired CIs, CI-type mismatches, unknown CIs,
  and **destructive actions on cluster-member datastores**. Governed by a **single admin-editable
  `ValidationPolicy`** every execution consults. The simulated CMDB gained CI type / lifecycle /
  cluster data; catalog items carry the metadata; approval stamps the review date. New
  `/governance/validation/policy|check|review-status` endpoints + a **pruning/review dashboard**
  (fresh / stale / never-reviewed + oldest). 119 backend tests.

### Security
- **WebSocket auth**: job-log and canvas-run streams now require a valid JWT (`?token=` query
  param); unauthenticated stream connections are rejected. Closes the last security-audit item.
- **Gate now covers canvas `automation_task` nodes** (single-target ops) in addition to catalog +
  direct-job paths; added an advisory `npm audit` step to CI.
- **Audit S2 — login throttling**: repeated failed logins are rate-limited (5 failures / 5 min
  per username → 429; cleared on success).
- **Central gate extended**: the `/api/v1/jobs/execute` direct path now also runs the CMDB
  lifecycle-consistency gate on its target (ad-hoc jobs to retired/cluster/unknown CIs are
  rejected) — not just catalog runs.
- **Audit S3 hardening**: security-response headers (CSP, `nosniff`, frame-deny, referrer) + a
  request body-size limit (413), and an **SSRF guard** on the `http_request` canvas node that
  blocks loopback/private/link-local/cloud-metadata targets (override via `NEXUS_HTTP_ALLOW_PRIVATE`).
- **Audit S1/S2 fixes**: job execution, queries, telemetry, and canvas run now **require
  authentication**; live-vs-check execution is **entitlement-checked**; the auditable
  `initiated_by` is **derived from the token** (client-supplied executor is ignored — anti-spoof);
  and the app **refuses to boot** a non-local/test environment on the default JWT secret. Tests
  cover unauth rejection + anti-spoof. (Remaining S-items tracked in the audit doc.)

### Added
- **Four formal audit reports** (`specs/audits/`): security & compliance, code quality,
  architecture/scalability/performance, and best-practice/linting/maturity — each with rated
  findings, a remediation plan, and a checklist, plus a consolidated remediation order.
- **M16 Incident / Error Kanban** (`incident_management` context): failed jobs **and** workflow
  runs auto-open an **incident card** (de-duplicated per source) on a triage board
  (New → Triage → Investigating → Resolved). Move cards, and **convert an incident → a draft
  remediation workflow** on the canvas (one click). `/api/v1/incidents/board|move|remediate` +
  a frontend kanban board. 107 backend tests.
- **M15 Governed workflow submission & review**: operators **submit** a composed workflow for
  review; engineers/admins **approve / request changes / reject** with comments via a Governance
  **review inbox**. Workflows carry a `review_state` (draft→submitted→…→approved/published) and a
  full review audit trail; graph edits preserve review state. Canvas gains a "Submit for review"
  action. `/api/v1/canvas/workflows/{id}/submit|review`, `/canvas/reviews/pending`. 100 tests.
- **M14 Catalog-at-scale UX** (`frontend/`): a faceted Service Catalog (domain/vendor facets with
  counts + type-ahead search, grouped cards with risk pills and atomic/orchestrated badges) and an
  **automation detail drawer** with tabs — Overview (rendered Markdown docs + prerequisites +
  tags), Parameters, and an **animated Logic-Flow SVG** of the automation's phases. Reusable
  `Markdown` + `LogicFlow` components.

- **3.0 operator-experience vision** (`specs/00_foundation/vision_operator_experience.md`): a
  fresh from-the-operator rethink — service catalog at scale, understand-before-you-run,
  governed Lego composition, incident kanban, and a believable large catalog.
- **M13 Connector ecosystem + rich catalog**: new simulation connectors **VMware (VCF 9)**,
  **Pure Storage (FlashArray)**, and **Cohesity** (each with realistic actions + streamed logs);
  catalog templates gained operator metadata (**domain, vendor, tags, risk tier, est. duration,
  prerequisites, version, atomic/orchestrated**); faceted list filtering (`domain`/`vendor`/
  `search`) + `/catalog/facets`; and a **27-item multi-vendor seed catalog** (VCF, Pure,
  Cohesity, ServiceNow-via-Ansible, Ansible, Terraform, scripts) where every item runs. 95 tests.

### Changed
- **CI hardening**: `runs-on: self-hosted` (drop the custom label so a vanished runner label can't
  hang CI), plus `PYTHONDONTWRITEBYTECODE` + `pytest -p no:cacheprovider` so the runner workspace
  stays clean for `actions/checkout`.

## [2.0.0] - 2026-06-18

The **ops-engineering management layer**: Nexus 2.0 wraps execution in governed change and
scheduling, so operations administers the *process* up front and Nexus automates the rest. Driven
by the objective review in `specs/00_foundation/vision_2_0.md`.

### Added
- **Change Management** (M10, `change_management` context, ADR-0005): reusable change templates
  (standard ITSM fields + CAB flag), per-resource change-control policies (`auto_change_control`,
  `change_template_id`, `require_approved_change`), and change records (CHG numbers + lifecycle).
  The catalog execute path opens a change per policy and stamps the change number onto the job;
  CAB-required changes block live runs until approved. `/api/v1/change` (engineer-gated). Jobs
  gained an optional `change_number`.
- **Scheduling** (M11, `scheduling` context): schedule workflows on interval or daily triggers
  with optional **maintenance windows**; a background ticker dispatches due schedules through the
  canvas. `/api/v1/schedules` CRUD + run-now.
- **Governance UI** (M12): a frontend Governance surface for change templates, change records
  (audit table), and schedules (create/run/delete).
- 88 backend tests; full backend + frontend CI green.

### Notes
- Continuing on the roadmap beyond 2.0: deeper policy-as-config (theme C), platform-builder /
  connector-SDK UX (E), and cross-functional features — drift, promotion, notifications (F).

## [1.0.0] - 2026-06-18

The MVP (`$ONE_POINT_OH`): a working, simulation-backed Automation Control Plane an operator can
authenticate to, browse, compose on a visual canvas, and run end-to-end with live logs and
governance — verified against a live server. Built as DDD vertical slices across six bounded
contexts with a self-hosted CI gate.

### Added
- **Connectors** (M2): vendor-agnostic ports (`ExecutionConnector`, `DiscoveryPort`,
  `SecretLeasePort`, `ApprovalPort`, `TelemetryPort`) + simulation adapters for
  Ansible/Terraform/script and ServiceNow/CyberArk/Dynatrace, a registry, and the `/connectors`
  API that powers the canvas connector dropdown.
- **Execution engine** (M3): job lifecycle state machine, persisted runs + log streams,
  in-memory broker + `WS /jobs/{id}/stream` (with replay), telemetry endpoint, and 50+ seeded
  historical runs.
- **Identity & Access** (M4): users/orgs/teams RBAC with capability matrix + entitlement
  evaluation, PBKDF2 + JWT auth (no native deps), `auth/login|me|users`, seeded demo users.
- **Automation Catalog** (M5): governed building blocks — templates, survey schemas, approval
  lifecycle, and execute-from-template (RBAC-checked).
- **Orchestration Canvas** (M6): the ported Foundry DAG engine re-targeted to connectors —
  parallel execution, condition/switch routing with skip propagation, per-node retries and error
  branches, approval gates (pause/resume), 15 node types incl. all backend-integration nodes,
  workflow/version/run persistence, and `WS` run streaming.
- **Frontend** (M7/M8): JWT auth, dashboard, catalog (+execute), live-streaming console, admin,
  and the visual canvas (pan/zoom, palette, port connections, connector dropdown, run
  highlighting, approval overlay).
- **Containerization** (M9): multi-stage rootless `Dockerfile` (single container serving SPA +
  API), `docker-compose.yml`, and the project README.

### Notes
- Pre-1.0 foundations (specs, DDD architecture, CI runner, platform skeleton) shipped in 0.1.0.
- Deferred to post-1.0: remaining canvas source node types (iterator/code/llm/tool/knowledge —
  issue #19) and live container-image build verification (Docker Desktop daemon flakiness).

## [0.1.0] - 2026-06-18

First tagged milestone (M1): foundation specs (DDD vertical slices + Canvas Orchestration), the
self-hosted CI gate, the backend platform skeleton (FastAPI + WAL SQLite + `shared_kernel` /
VariablePool), and the React/Vite/Tailwind frontend shell. See ADRs 0001–0004.

# ADR-0013 — GitOps config backbone

**Status:** Accepted (2026-06-20)

## Context

The operator's requirement ([vision](../00_foundation/vision_deterministic_governance.md) §6): Nexus
should **version and back up its own configuration** in Git — a system-of-record + DR mechanism +
environment-promotion path. All of Nexus's config is already data (workflows, CMDB schemas + lineage,
pinning rules, themes, validation policy, change templates, schedules), so it can live as code.

Constraints (project guardrails): **no paid/remote services**; **no secrets in the repo**; must work
on the dev/CI host (where git identity may be unset) and degrade gracefully where git is absent.

## Decision

A new **`gitops`** context provides config-as-code over a **local Git repo**:

1. **Canonical serialization** — a deterministic snapshot (`{path: content}`) with stable file paths
   and sorted-key JSON, **volatile audit timestamps stripped**, so re-serializing unchanged config is
   byte-identical (no spurious diffs).
2. **VersioningPort + LocalGitRepo adapter** — official git via subprocess in a configured local dir
   (`config_repo_dir`, default `./data/config-repo`, gitignored). `commit()` mirrors the desired file
   set (deleting dropped artifacts), is **idempotent** (no commit when unchanged), runs with a fixed
   `-c user.*` identity (so CI commits) and `core.autocrlf=false` + UTF-8 decoding (so content stays
   byte-identical across OSes). `available()` is False when git is missing — the platform is unaffected.
3. **GitOpsService** — `sync(actor)` serializes + commits on change (audit message: actor/what), on
   the scheduler cadence (`gitops_sync_every`) and on demand; `history/diff/restore`; and a
   `pull_preview()` that diffs the repo HEAD (desired) against the live snapshot for an optional,
   admin-gated reconcile.
4. **API + admin UI** — status, "back up now", per-artifact history/diff/restore, pull-preview.

**Local-only by default.** Pointing at a remote and full pull→apply reconciliation are explicit
future extensions; nothing here reaches the network.

## Consequences

**Good**
- Deterministic, auditable, **revertable** configuration + a DR backup, with no bespoke export/import.
- Idempotent sync means continuous backup without commit noise; byte-stable snapshots make diffs real.
- Builds on the K45 export bundle conceptually; reuses the existing scheduler cadence.

**Bad / costs**
- Subprocess git is environment-sensitive (newline/encoding/identity) — handled, but a pure-python
  git lib would avoid the binary dependency (rejected to keep to official tooling, no new deps).
- `pull_preview` reports the desired-vs-live delta; **applying** a pull (importing repo state into
  live) is left as an admin-gated follow-up to avoid a risky auto-overwrite path in the POC.

## Alternatives considered
- **dulwich / pygit2 (pure-python git)** — viable and avoids the binary, but adds a dependency; the
  subprocess adapter behind a port keeps options open and uses official git.
- **Just the K45 JSON export bundle** — insufficient: no history/diff/restore, no idempotent backup,
  no reconcile; the bundle is a point-in-time dump, not a versioned system-of-record.

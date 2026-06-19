# Audit 4 — Code Best-Practice, Linting, Maturity & Correctness

**Date:** 2026-06-19 · **Status:** report. Findings rated **B1 (high) → B4 (low)**.

## What's solid
Ruff (lint + format, rules E/F/I/UP/B/W) and ESLint flat config + strict `tsc` are enforced in CI
on every PR. Conventional Commits, ADRs, CHANGELOG, and traceable issues are followed. Backend is
fully type-annotated; domain layers are pure.

## Findings

### B1 — No static type checking in CI
Backend has type hints but **no mypy/pyright gate** — type regressions can slip in. → Add
`mypy` (or pyright) to the backend CI job; start lenient, tighten over time.

### B2 — No security/static-analysis linter
Ruff doesn't run the `S` (flake8-bandit) rules. → Enable ruff `S` selectively (the one real
`eval` in VariablePool is already restricted + documented; add `# noqa: S307` there and let `S`
catch new issues).

### B2 — Coverage not enforced
107 backend tests but no coverage floor. → `pytest-cov` with a threshold (e.g. 80%) once measured.

### B3 — Broad `except Exception` sites
Several `# noqa: BLE001` best-effort catches (broker publish, incident capture, jinja render).
Intentional and annotated, but each should log at warning (most do). → Audit each for a
swallowed-error path; ensure all log.

### B3 — Frontend test depth & a11y
One vitest test; no accessibility checks. → Add component tests and basic a11y lint
(eslint-plugin-jsx-a11y) for the operator UI.

### B3 — Structured logging / observability of the platform itself
Uses stdlib `logging` without structured config; no platform metrics endpoint. → Configure JSON
logging + a `/metrics` (or reuse health) for self-observability (ties to vision theme E/F).

### B4 — Magic numbers / config sprawl
Concurrency (5), prune-keep (50), PBKDF2 iterations (120k), jitter bounds are inline constants.
→ Surface the operationally-relevant ones in `Settings`.

### B4 — OpenAPI/docs polish
FastAPI auto-docs exist at `/docs`; endpoints lack rich descriptions/examples and consistent
tags in a few places. → Add summaries/examples; group tags.

## Plan / checklist
- [ ] Add mypy (or pyright) to CI (lenient → strict). *(next)*
- [x] Enable ruff `S` (flake8-bandit) rules; deliberate exceptions documented in pyproject; the
      known `eval` is `# noqa: S307`; the lone `assert` replaced with a real guard.
- [x] Add pytest-cov (reporting in CI; **91%** at adoption). Threshold gate to follow.
- [ ] Review broad-except sites for logging.
- [ ] Frontend component tests + jsx-a11y.
- [ ] Structured logging + platform self-metrics.
- [ ] Move inline constants into Settings; enrich OpenAPI docs.

---

## Consolidated remediation order (all four audits)
1. **Security S1/S2** — auth coverage on execution routes, server-derived `initiated_by`, JWT
   guard, central execution gate. *(highest priority — do first)*
2. **Architecture A1** — document single-instance ceiling + startup recovery sweep.
3. **Quality Q2** — shared `fresh_db` fixture + `AsyncBroker` extraction.
4. **Best-practice B1/B2** — mypy + ruff `S` + coverage in CI.
5. Remaining S3/S4, A2–A4, Q3–Q4, B3–B4 as follow-on issues.

Each item ships as its own branch → TDD → green CI → merge, referencing the audit it resolves.

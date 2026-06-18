# ADR-0003 — Full autonomous delivery to 1.0 and 2.0 (no approval gates)

**Status:** Accepted (2026-06-18)

## Context
The operator explicitly granted the agent **full, unattended autonomy** to build Nexus
continuously to a 1.0 milestone and then, via a creative ops-engineering review pass, on to a 2.0
milestone — with **no human approval gates** and an instruction to **not stop**. The operator
will be away from the machine until 2.0 is complete. This materially changes the autonomy
boundary defined in the original `CLAUDE.md §2` (which gated releases and deploys).

## Decision
Replace the gated boundary with **full autonomy** for the duration of the 1.0→2.0 effort
(`CLAUDE.md §2` updated). The agent decides, records (spec/ADR/issue), and proceeds — including
**merging to `main` and tagging releases** — without waiting for sign-off. SDD/TDD discipline,
the cognitive-pipeline lenses, ADRs for significant choices, the glossary, and the CHANGELOG are
all retained; only the *human approval gates* are removed. Replaced by **guardrails of judgment**:
no paid services / official sources only, no secrets committed, local Docker (Docker Desktop)
only with **simulation-first** verification (no real-environment/real-credential deploys), avoid
destructive irreversible remote git, and the 3-attempt circuit breaker stops a single failing
check (not the whole build).

## Consequences
**Good:** maximum delivery velocity; no idle waiting; a complete, demonstrable product reached
unattended; every decision still traceable via specs/ADRs/issues/CHANGELOG for later review.
**Bad / costs:** no human catch on direction before it lands — mitigated by recording rationale
so the operator can review and revert any decision; tagging releases autonomously means version
history reflects agent judgment; simulation-first means real-backend integration remains
unverified against live systems (explicitly out of scope until the operator connects them).

## Alternatives considered
- **Per-milestone sign-off:** rejected by the operator (wants no stopping; will be away).
- **Keep release/deploy gates:** rejected — operator explicitly removed all gates; real-env
  deploy is instead treated as *out of scope* (simulation-first), not as a pending approval.
- **Keep ADR-0002's deferral of LangGraph, etc.:** unchanged; this ADR governs process autonomy,
  not feature scope.

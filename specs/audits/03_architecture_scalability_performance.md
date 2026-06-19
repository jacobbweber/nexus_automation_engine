# Audit 3 — Architecture, Design, Scalability & Performance

**Date:** 2026-06-19 · **Status:** report. Findings rated **A1 (high) → A4 (low)**.

## What's solid
DDD vertical slices with clean context boundaries; the connector **port/adapter** seam makes the
system genuinely vendor-agnostic; spec-first + ADRs keep design legible. The harvested
event-driven-pull lessons are documented even if not yet fully realized here.

## Findings

### A1 — Single-process runtime state blocks horizontal scale
Live log fan-out (`LogBroker`/`RunBroker`), `pending_approvals`, the scheduler ticker, and
background `asyncio.create_task` runs all live **in one process**. Behind a load balancer or with
>1 replica: WebSocket clients miss events from other instances, approvals can't resolve
cross-instance, and the scheduler double-fires. → For scale, adopt the **event-driven pull
architecture** (central DB queue, stateless API, separate runner) — already on the backlog from
the Ava harvest. Document the current **single-instance ceiling** explicitly.

### A1 — In-flight runs are not crash-recoverable  ✅ (sweep done)
A job/workflow marked RUNNING is lost if the process restarts (no requeue/resume). → **Done:** a
startup **recovery sweep** marks orphaned PENDING/RUNNING jobs and RUNNING workflow runs as FAILED
(`JobRepository.fail_orphaned_running` / `CanvasRepository.fail_orphaned_runs`, called in the app
lifespan) so persisted state is honest after a restart. Requeue/resume remains future work.

> **Single-instance ceiling (documented):** live log fan-out, approvals, the scheduler, and
> background run tasks are in-process. Run **one** API instance until the event-driven-pull
> split lands; the recovery sweep keeps state consistent across restarts of that instance.

### A2 — SQLite single-writer ceiling
SQLite/WAL is great for the POC but is a single-writer store. At real concurrency it bottlenecks.
→ Plan a Postgres profile behind the same repository interfaces (the repos already abstract it);
keep SQLite for local/demo. (ADR-0004 documents the sync choice; a Postgres ADR would follow.)

### A2 — Scheduler has no leader election
The ticker assumes one instance. → DB-claim (`BEGIN IMMEDIATE`) or a leader lock before
dispatch when multi-instance.

### A3 — Python-side aggregation that should be SQL
`catalog.facets()` and `incident.board()` load all rows then group in Python. Fine at hundreds;
at thousands use `GROUP BY` / indexed filters. Indices exist on key columns (good).

### A3 — Pagination missing on list endpoints
`/jobs`, `/canvas/workflows`, `/incidents`, `/catalog/templates` return capped-but-unpaginated
lists. → Add `limit`/`offset` (or cursor) params + total counts for the UI at scale.

### A4 — Background task references not retained
`asyncio.create_task(...)` results aren't stored; tasks can be GC'd under some loops and there's
no shutdown drain. → Keep a task set; drain on shutdown; (mostly mitigated by the run persisting
its own state, but worth hardening).

### A4 — Connector calls are sequential within a node
Fine today; for fan-out (e.g. iterate hosts) the engine already supports parallel branches via
the semaphore. Revisit the `iterator` node (deferred, #19) for large arrays.

## Plan / checklist
- [ ] Document single-instance ceiling in architecture.md; ADR for the scale path.
- [ ] Startup recovery sweep for orphaned RUNNING jobs/runs.
- [ ] Postgres profile behind repositories (design + ADR).
- [ ] Scheduler DB-claim / leader lock.
- [ ] SQL aggregation for facets/board; pagination on list endpoints.
- [ ] Retain + drain background tasks on shutdown.

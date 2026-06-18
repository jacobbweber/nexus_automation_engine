# ADR-0004 — Synchronous SQLAlchemy for the database layer

**Status:** Accepted (2026-06-18)

## Context
`architecture.md §7` called for async-first SQLAlchemy (aiosqlite). In practice, async
SQLAlchemy requires the **greenlet** native extension, and on the development machine **and** the
self-hosted CI runner (the same Windows host) greenlet's compiled DLL is **blocked by Windows
Application Control** (`DLL load failed while importing _greenlet: An Application Control policy
has blocked this file`). This is an environment security policy we do not control and should not
attempt to disable. With greenlet unavailable, an async DB engine cannot initialize at all, so
tests and the app fail at startup.

## Decision
Use **synchronous SQLAlchemy** over the stdlib `sqlite3` driver for the database layer (no
greenlet). Preserve responsiveness by declaring DB-bound route handlers as `def` so FastAPI runs
them in its threadpool, and keep `async` where it provides real value and does **not** need
greenlet — connectors (httpx), WebSocket log streaming, and the asyncio execution worker. All
connections still get WAL + busy_timeout + `synchronous=NORMAL` + foreign keys via the single
`database.py` helper. `database_url` default becomes `sqlite:///./nexus.db`.

## Consequences
**Good:** the stack runs on the actual dev/CI host with no native-DLL policy conflict; sync
SQLAlchemy + FastAPI threadpool is a well-trodden, robust pattern; the WAL concurrency guarantees
are unchanged; simpler mental model for repositories.
**Bad / costs:** DB calls occupy threadpool threads rather than the event loop (fine at this
scale; revisit if DB concurrency becomes a bottleneck); a deployment target without the greenlet
block (e.g. OpenShift) can't use async DB without reverting this — acceptable, and revisitable
via a superseding ADR if/when we deploy there.

## Alternatives considered
- **Async SQLAlchemy + aiosqlite (original plan):** blocked by Application Control on greenlet.
- **Disable/whitelist the Application Control policy:** out of scope, no admin, and a security
  control we shouldn't weaken.
- **A non-SQLAlchemy async driver:** more churn for no benefit while greenlet is blocked; SQLite
  is the chosen store and sync access fits it well.

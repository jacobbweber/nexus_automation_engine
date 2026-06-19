# Audit 2 — Code Quality & Analysis

**Date:** 2026-06-19 · **Status:** report. Findings rated **Q1 (high) → Q4 (low)**.

## Findings

### Q2 — Duplicated infrastructure boilerplate
- Two near-identical brokers: `execution_engine.application.broker.LogBroker` and
  `orchestration_canvas.application.broker.RunBroker`. → Extract a generic `AsyncBroker` into
  `shared_kernel` (was a deliberate decoupling at the time; now worth DRYing).
- Every repository repeats `with get_sessionmaker()() as s: ...`. → A small `@unit_of_work`
  helper / session context would cut noise.
- Each simulation connector repeats the `_line()` + `_FLOWS` + execute loop. → A shared
  `flow_connector` builder in `simulation/_support.py` would collapse vmware/pure/cohesity.

### Q2 — Test setup duplication
Many context tests re-implement the same `_ensure_schema()` (reset → import ORMs → drop/create).
→ Provide a shared `fresh_db` fixture (autouse-opt-in) in `conftest.py` that imports all ORM
modules once and recreates the schema. Reduces ~15 copies to one.

### Q3 — Inconsistent datetime tz handling
Scheduling coerces SQLite-naive datetimes back to UTC-aware on read; other contexts return naive
datetimes from the DB. → Standardize: a single `DateTime(timezone=True)` type decorator or a
shared `_aware()` coercion in the base/read path.

### Q3 — Stringly-typed fields
`source_type` ("job"/"workflow"), review `decision`, change close codes are bare strings. →
Promote to `StrEnum`s for safety + discoverability.

### Q3 — No coverage measurement
Tests are broad but coverage isn't tracked. → Add `pytest --cov` (coverage.py) and a soft
threshold in CI; surface the number.

### Q4 — Service instantiation per request
Routes do `CanvasService()` per call. Cheap (no heavy state) but a DI provider (FastAPI
`Depends`) would aid testability/mocking.

### Q4 — Frontend test depth
Only one frontend test (the auth gate). → Add component tests for catalog filtering, the canvas
reducer logic, and incident board rendering.

## Plan / checklist
- [x] Extract `AsyncBroker` to `shared_kernel`; execution + canvas brokers are thin singletons
      over it (LogBroker/RunBroker kept as aliases).
- [ ] Shared `fresh_db` test fixture; delete per-file `_ensure_schema` copies. *(low-value churn;
      deferred)*
- [ ] Standardize tz-aware datetime reads.
- [ ] Enum-ize `source_type` / review decision / close codes.
- [ ] Add coverage reporting to CI.
- [ ] Add a `flow_connector` helper; refactor vendor adapters.
- [ ] Add frontend component tests.

# Audit 1 — Security & Compliance

**Date:** 2026-06-19 · **Scope:** whole repo (backend, frontend, CI, container) · **Status:** report

This is an honest security review of the codebase as built. Findings are rated **S1 (critical) →
S4 (low)**. A remediation plan + checklist follows; items are then executed under the normal
branch→TDD→green-CI→merge flow.

---

## Findings

### S1 — Execution endpoints are unauthenticated
`POST /api/v1/jobs/execute`, `GET/WS /jobs/*`, `POST /canvas/workflows/{id}/run`, the canvas WS,
`/connectors/*` discovery, and `/telemetry/*` have **no auth dependency**. Anyone who can reach
the API can run automation (including production-affecting connectors) and read run data. Only
auth/catalog-author/change/schedule/review carry `Depends`. **This is the top issue.**
→ Require `get_current_user` on all state-changing and data-exposing routes; enforce
`can_execute` entitlement on job/canvas execution.

### S1 — Auditable executor is client-supplied (spoofable)
`JobSubmission.initiated_by` and canvas run actor come from the request body / default, not the
authenticated token. The audit trail ("who ran this") can be forged. → Derive `initiated_by`
from `UserContext` server-side; ignore client-supplied actor.

### S2 — JWT secret defaults to a dev placeholder
`config.jwt_secret` has a hardcoded dev default. If `NEXUS_JWT_SECRET` is unset in a real
environment, tokens are forgeable. → Fail fast at startup if `environment != local` and the
secret is the default; document required env.

### S2 — No brute-force protection on login
`/auth/login` has no rate limiting or lockout. → Add simple per-username/IP throttling
(in-memory token bucket) and a constant-time failure path (already constant-time on hash compare).

### S2 — Change-control gate is bypassable
`require_approved_change` is enforced only in `catalog.execute`. Direct `POST /jobs/execute` and
canvas `automation_task` execution skip it. → Centralize change-control + entitlement checks in
the execution boundary so every path is gated (ties into the CMDB-validation feature).

### S3 — SSRF via `http_request` canvas node
The `http_request` node fetches an operator-supplied URL from inside the platform → SSRF to
internal/metadata endpoints. → Allowlist schemes/hosts (config), block link-local/metadata
ranges; mark the node as engineer-only.

### S3 — Frontend dependency vulnerabilities
`npm install` reported 5 advisories (3 moderate / 1 high / 1 critical) in transitive deps.
→ Triage with `npm audit`, bump/resolve; add a (non-blocking at first) CI audit step.

### S3 — No security headers / request size limits
No `Content-Security-Policy`, `X-Content-Type-Options`, or body-size limits. → Add a security
middleware (headers + max body size).

### S4 — Secret handling (verified OK, harden docs)
CyberArk lease secret is masked in persisted step outputs and the pool isn't persisted; step
`inputs` store node templates (`{{ref}}`), not resolved secrets. Good. → Add a regression test
asserting secrets never reach persisted rows/logs; document the guarantee.

### S4 — Tokens not revocable; long-lived
JWT has no jti/denylist; logout is client-side only. → Acceptable for POC; note for production
(short TTL + refresh + denylist).

### Compliance posture (positive)
RBAC model, change records (CHG), approval gates, and the incident trail give a solid auditable
spine. Gaps above are about *enforcement coverage*, not absence of controls.

---

## Remediation plan (priority order)

1. **AuthN/Z coverage (S1):** add `get_current_user` to all execution/data routes; enforce
   `can_execute` on job + canvas execution; derive `initiated_by` from the token. *(tests per route)*
2. **JWT secret hardening (S2):** startup guard; docs.
3. **Login throttling (S2).**
4. **Central execution gate (S2):** single choke point applying entitlement + change control for
   every execution path (designed alongside the CMDB-validation feature).
5. **SSRF allowlist + engineer-only http node (S3).**
6. **Security headers + body limit middleware (S3).**
7. **`npm audit` triage + CI step (S3).**
8. **Secret-never-persisted regression test + docs (S4).**

## Checklist
- [x] S1 route auth coverage on job execution + queries + telemetry; entitlement on execute
      (`get_current_user` + `has_capability`); canvas run requires auth.
- [x] S1 server-derived `initiated_by` (token identity overrides client input; test asserts
      anti-spoof).
- [x] S2 JWT default-secret startup guard (refuses to boot non-local/test on the dev secret).
- [ ] S1 (remaining) WebSocket auth via query-param token; entitlement on canvas run; auth on
      catalog/connectors browse.
- [x] S2 login throttling (in-memory: 5 failures / 5 min per username → 429; cleared on success).
- [x] S2 centralized execution gate — the M18 lifecycle-validation gate enforces metadata + CMDB
      consistency on the catalog execute path (extend to direct /jobs + canvas next).
- [x] S3 SSRF guard on the `http_request` node (blocks loopback/private/link-local/metadata;
      `NEXUS_HTTP_ALLOW_PRIVATE` to override).
- [x] S3 security-headers + body-limit middleware (CSP, nosniff, frame-deny, referrer; 413 on
      oversized bodies).
- [ ] S3 npm audit triage + CI
- [x] S4 secret-non-persistence regression test (lease masked in output; real secret only in the
      pool for downstream use).
- [x] Extend the execution gate to **direct `/jobs/execute`** (CMDB-consistency gate on the
      target; catalog path keeps full metadata validation).
- [x] Extend the gate to canvas `automation_task` nodes (single-target ops).
- [x] S3 `npm audit` advisory step in CI.
- [x] WebSocket token auth (JWT via `?token=` query param; unauthenticated streams rejected).

**Security audit: all findings resolved.**

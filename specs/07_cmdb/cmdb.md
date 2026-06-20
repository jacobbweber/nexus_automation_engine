# CMDB Schema & Lineage — context spec

**Context:** `cmdb` (new in v4.0) · **Decision:** [ADR-0009](../adr/ADR-0009-cmdb-schema-and-lineage-context.md)
· **Pillar A** of [vision_deterministic_governance.md](../00_foundation/vision_deterministic_governance.md).

## Goal

Make the CMDB a **schema-enforced contract**: define, per CI type, the fields and the typed
**lineage** (required relationships) that make a CI "healthy", and check any CI against that
definition **deterministically**. This drives how CIs should be defined and is the foundation the
lifecycle gate, deterministic pinning, and review-impact build on.

## Use cases & value

- An **admin/integrator** defines what a `vm` (or `datastore`, `cluster`, …) must contain and how it
  must relate to other CIs — once, as data — and maintains it over time (CMDB Schema Studio).
- The **platform** checks any CI against its schema + lineage and produces a **CI Health Report**
  (gaps + score + remediation), used by the lifecycle gate, target pickers, and pinning.
- An **operator** sees, before running, whether the target CI is healthy and what its lineage is.

## Domain model

- **FieldDef** — `name`, `label`, `datatype` (`string|integer|boolean|enum|datetime|reference`),
  `required`, `allowed_values?` (enum), `regex?`, `default?`, `sensitive?`.
- **CITypeSchema** — `type` (e.g. `vm`), `label`, `version`, `description`, `fields[]`,
  `required_tags[]`, `naming_pattern?` (regex on `name`), `updated_by/at`.
- **LineageRelationship** (24.2) — `name`, `target_type`, `direction` (`up|down`), `cardinality`
  (`one|many`), `required`.
- **LineageSpec** (24.2) — `type`, `relationships[]`.
- **CIHealthReport** (24.3) — `ci_id`, `ci_type`, `status` (`healthy|degraded|unhealthy`), `score`
  (0–100), `field_issues[]`, `lineage_issues[]`, `tag_issues[]`, `remediation_hints[]`.

**Invariants.** Field names are unique within a schema; enum fields declare `allowed_values`;
`regex`/`naming_pattern` must compile; lineage `target_type` must reference a known CI type; no cycle
in required `up` relationships. Enforced by a pure `validate_schema` / `validate_lineage`.

## Application contracts (api)

- `GET /cmdb/schemas` · `GET /cmdb/schemas/{type}` · `PUT /cmdb/schemas/{type}` (admin, validated)
- `GET /cmdb/lineage/{type}`
- `POST /cmdb/validate-ci` → CI Health Report for an ad-hoc record
- `GET /cmdb/ci/{id}/health` → fetch CI via the ServiceNow ACL connector + related, run the checker

## UX behavior

- **CMDB Schema Studio** (admin): define/edit fields + tags + naming + lineage with live
  deterministic validation (mirrors Theme Studio).
- **CI health badges** in CMDB-lookup nodes and target pickers; a **Lineage Explorer** rendering a
  CI + required relationships with gaps highlighted.

## Acceptance criteria

- CI type schemas + lineage are definable, seeded, retrievable, and versioned; malformed definitions
  are rejected with clear messages.
- Any CI can be checked → a deterministic health report (stable score + hints).
- The lifecycle-validation gate consults the checker (policy-gated).
- Admin can author schemas in-app; CI health is visible in pickers and a Lineage Explorer.

## Open questions

- Canonical CI-type vocabulary vs the simulated CMDB's current `server`/`datastore` values
  (standardize toward `vm`; enrich the sim additively).
- How much relationship data the simulated CMDB should carry for believable lineage checks.

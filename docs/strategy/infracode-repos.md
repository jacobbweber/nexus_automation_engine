# Org & repo strategy — infracode pillar repos

How the *automation content* is organized in source control, and how it relates to Nexus.

## Two kinds of repo (keep them separate)

1. **infracode pillar repos** — the **automation content** itself, one mono/pillar repo per
   integration:
   - `infracode_ansible` — playbooks, roles, job-template definitions.
   - `infracode_terraform` — modules, workspaces, environment configs.
   - `infracode_snow` — ServiceNow artifacts (catalog items, flows, CMDB definitions).
   - `infracode_pure` — Pure Storage automation (volumes, protection groups).
   - `infracode_cisco` — network automation (NSO/Cisco device configs).

2. **The Nexus platform-config repo** — the **GitOps backbone** (M28): Nexus's *own* configuration
   (workflows, CMDB schemas, pinning rules, policies, schedules, themes) serialized as code. This is
   generated and committed by Nexus; humans don't hand-edit it. Keep it distinct from infracode.

> Nexus *references/consumes* infracode (a building block points at an Ansible job template that lives
> in `infracode_ansible`); it *owns* the platform-config repo. infracode is not a runtime dependency
> of the POC (connectors are simulated), but the strategy below is how a real deployment maps.

## Per-pillar structure (recommended)
```
infracode_<vendor>/
├── README.md                # ownership, scope, how to contribute
├── CODEOWNERS               # the automation team(s) accountable for this pillar
├── <unit>/                  # one folder per atomic unit (playbook/module/...)
│   ├── main.*               # the automation
│   ├── meta.yaml            # maps to a Nexus catalog block: idempotency, plain_summary, ci_type, risk
│   └── tests/               # unit/contract tests for the unit
└── environments/            # env-specific variables (no secrets — secrets come from the vault)
```

## Branching & release
- **Trunk-based**: short-lived branches → PR → review → merge to `main`; tag releases per pillar.
- A unit's `meta.yaml` is the contract Nexus imports (so a block's idempotency/plain-summary/ci_type
  are authored *with the code*, versioned together).
- **Promotion** across environments is a Git operation (merge/tag), mirrored by Nexus's own
  config-repo (GitOps) for the platform side.

## Deterministic naming & tagging conventions
These make everything reproducible and machine-checkable (enforced by the CMDB schema + lineage):
- **CI naming**: lowercase, hyphenated, environment-prefixed where useful — e.g. `web-prod-01`,
  `ds-vvol-01`, `esx-prod-01`. Each CI type declares a `naming_pattern` (regex) in its schema.
- **Required tags** (per CI type): `owner`, `team`, `environment`, `cost_center`, plus type-specific
  (`backup_tier`, `DR-Tier`, `criticality`). The health checker flags missing/invalid tags.
- **Automation units** map 1:1 to catalog blocks; the block id/name is stable and references the
  infracode unit path.
- **No secrets in any repo** — credentials are leased at runtime (CyberArk port); commit messages and
  config carry the *actor*, never credentials.

## Why separate infracode from platform-config
- Different audiences/cadence: infracode changes when automation logic changes; platform-config
  changes when *governance* (workflows/rules/schemas) changes.
- Different ownership: pillar teams own infracode; platform admins own the Nexus config repo.
- Clean blast radius: a bad infracode change can't corrupt the governance record, and vice-versa.

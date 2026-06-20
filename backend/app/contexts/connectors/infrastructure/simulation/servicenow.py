"""Simulated ServiceNow connector — CMDB discovery + change/request approval validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.contexts.connectors.domain.models import (
    Capabilities,
    ChangeValidation,
    ConnectorAction,
    ConnectorCategory,
    ConnectorKind,
    DiscoveryQuery,
    ParamField,
    Resource,
)


# A small, believable CMDB the discovery adapter filters over. Each CI carries a ci_type,
# lifecycle_state, and cluster membership so lifecycle-validation checks have real signal.
def _ci(id, name, ci_type, env, *, lifecycle="operational", cluster=None, os=None):
    row: dict[str, object] = {
        "id": id,
        "name": name,
        "fqdn": f"{name}.sim.internal",
        "ci_type": ci_type,
        "env": env,
        "lifecycle_state": lifecycle,
        "cluster_member": cluster is not None,
        "cluster": cluster,
    }
    if os:
        row["os"] = os
    return row


_CMDB: list[dict[str, object]] = [
    _ci("ci-1001", "web-prod-01", "server", "Production", os="RHEL9"),
    _ci("ci-1002", "web-prod-02", "server", "Production", os="RHEL9"),
    _ci("ci-1003", "app-stg-01", "server", "Staging", os="RHEL9"),
    _ci("ci-1004", "db-prod-01", "server", "Production", os="Windows2022"),
    _ci("ci-1005", "dev-box-07", "server", "Development", os="Ubuntu24"),
    _ci("ci-1006", "legacy-app-02", "server", "Production", lifecycle="retired", os="RHEL7"),
    # Storage CIs — datastores; some are members of a vSphere cluster.
    _ci("ci-2001", "ds-vvol-01", "datastore", "Production", cluster="wld-prod-01"),
    _ci("ci-2002", "ds-vvol-02", "datastore", "Production", cluster="wld-prod-01"),
    _ci("ci-2003", "ds-scratch", "datastore", "Development"),
]


def get_ci(name: str) -> dict[str, object] | None:
    for r in _CMDB:
        if r["name"] == name:
            return r
    return None


# CMDB tables exposed to the canvas CMDB-lookup field picker. Maps a ServiceNow-style table name
# to the CI types it holds, so the UI can offer "pick a table → pick its fields".
CMDB_TABLES: dict[str, list[str]] = {
    "cmdb_ci_server": ["server"],
    "cmdb_ci_storage_device": ["datastore"],
    "cmdb_ci": ["server", "datastore"],  # base table: all CIs
}

# Stable, documented field catalog for the picker (superset across CI types).
_CMDB_FIELDS: list[dict[str, str]] = [
    {"name": "id", "label": "CI sys_id", "type": "string"},
    {"name": "name", "label": "Name", "type": "string"},
    {"name": "fqdn", "label": "FQDN", "type": "string"},
    {"name": "ci_type", "label": "CI type", "type": "string"},
    {"name": "env", "label": "Environment", "type": "string"},
    {"name": "lifecycle_state", "label": "Lifecycle state", "type": "string"},
    {"name": "cluster_member", "label": "Cluster member", "type": "boolean"},
    {"name": "cluster", "label": "Cluster", "type": "string"},
    {"name": "os", "label": "Operating system", "type": "string"},
]


# Simulated change (CHG) records — the system of record for the change calendar. Windows are
# generated relative to "now" so the calendar always shows an upcoming schedule. (id, desc, state,
# day-offset, hour, duration-hours, assignment_group, risk, affected CI names)
_CHANGE_SEED: list[tuple] = [
    (
        "CHG0044820",
        "Rolling ESXi cluster patch — wld-prod-01",
        "scheduled",
        1,
        22,
        4,
        "Compute",
        "high",
        ["web-prod-01", "web-prod-02", "db-prod-01"],
    ),  # noqa: E501
    (
        "CHG0044833",
        "Pure FlashArray firmware upgrade",
        "scheduled",
        2,
        1,
        3,
        "Storage",
        "high",
        ["ds-vvol-01", "ds-vvol-02"],
    ),  # noqa: E501
    (
        "CHG0044851",
        "Cohesity backup policy rollout",
        "implement",
        3,
        20,
        2,
        "Backup",
        "moderate",
        ["db-prod-01"],
    ),  # noqa: E501
    ("CHG0044867", "ServiceNow MID server update", "scheduled", 5, 18, 1, "ITSM", "low", []),
    (
        "CHG0044872",
        "NSX firewall ruleset change",
        "scheduled",
        1,
        23,
        1,
        "Networking",
        "moderate",
        ["web-prod-01"],
    ),  # noqa: E501
    (
        "CHG0044890",
        "Datastore decommission — ds-scratch",
        "assess",
        7,
        2,
        2,
        "Storage",
        "high",
        ["ds-scratch"],
    ),  # noqa: E501
    (
        "CHG0044901",
        "Quarterly credential rotation",
        "scheduled",
        9,
        3,
        2,
        "Security",
        "moderate",
        [],
    ),  # noqa: E501
]


def list_changes() -> list[dict[str, object]]:
    """Return simulated CHG records (the change calendar's system of record)."""
    now = datetime.now(UTC)
    out: list[dict[str, object]] = []
    for num, desc, state, day, hour, dur, group, risk, cis in _CHANGE_SEED:
        start = (now + timedelta(days=day)).replace(hour=hour, minute=0, second=0, microsecond=0)
        out.append(
            {
                "number": num,
                "short_description": desc,
                "state": state,
                "start": start.isoformat(),
                "end": (start + timedelta(hours=dur)).isoformat(),
                "assignment_group": group,
                "risk": risk,
                "affected_cis": list(cis),
            }
        )
    out.sort(key=lambda c: str(c["start"]))
    return out


def impact(targets: list[str]) -> list[dict[str, object]]:
    """Blast-radius: the CIs an action on these targets would touch — each target CI plus, when it
    is a cluster member, its cluster siblings (a change to one ripples across the cluster)."""
    seen: dict[str, dict[str, object]] = {}
    for name in targets:
        ci = get_ci(name)
        if not ci:
            continue
        seen[name] = {
            "name": name,
            "ci_type": ci.get("ci_type"),
            "cluster": ci.get("cluster"),
            "reason": "direct target",
        }
        cluster = ci.get("cluster")
        if ci.get("cluster_member") and cluster:
            for row in _CMDB:
                rn = str(row["name"])
                if row.get("cluster") == cluster and rn not in seen:
                    seen[rn] = {
                        "name": rn,
                        "ci_type": row.get("ci_type"),
                        "cluster": cluster,
                        "reason": f"cluster sibling of {name}",
                    }
    return list(seen.values())


def cmdb_tables() -> list[str]:
    return list(CMDB_TABLES)


def cmdb_fields(table: str | None = None) -> list[dict[str, str]]:
    """Return selectable CI fields, optionally narrowed to those present in a table's CI types."""
    if not table or table not in CMDB_TABLES or table == "cmdb_ci":
        return _CMDB_FIELDS
    ci_types = set(CMDB_TABLES[table])
    present: set[str] = set()
    for row in _CMDB:
        if row.get("ci_type") in ci_types:
            present.update(row.keys())
    return [f for f in _CMDB_FIELDS if f["name"] in present]


class ServiceNowSimConnector:
    kind = ConnectorKind.SERVICENOW

    def capabilities(self) -> Capabilities:
        return Capabilities(
            kind=ConnectorKind.SERVICENOW,
            category=ConnectorCategory.SYSTEM_OF_RECORD,
            display_name="ServiceNow",
            description="CMDB inventory discovery and change/request approval validation.",
            streams_logs=False,
            actions=[
                ConnectorAction(
                    name="cmdb_lookup",
                    label="CMDB lookup",
                    params=[
                        ParamField(
                            name="table", type="string", label="Table", default="cmdb_ci_server"
                        ),
                        ParamField(
                            name="env",
                            type="select",
                            label="Environment",
                            choices=["", "Production", "Staging", "Development"],
                        ),
                        ParamField(name="limit", type="number", label="Limit", default=50),
                    ],
                ),
                ConnectorAction(
                    name="validate_request",
                    label="Validate request/change",
                    params=[
                        ParamField(
                            name="reference", type="string", label="RITM / CHG", required=True
                        ),
                        ParamField(
                            name="required_state",
                            type="string",
                            label="Required state",
                            default="approved",
                        ),
                    ],
                ),
            ],
        )

    async def discover(self, query: DiscoveryQuery) -> list[Resource]:
        env = query.filters.get("env")
        ci_type = query.filters.get("ci_type")
        name = query.filters.get("name")
        rows = [
            r
            for r in _CMDB
            if (not env or r.get("env") == env)
            and (not ci_type or r.get("ci_type") == ci_type)
            and (not name or r.get("name") == name)
        ]
        rows = rows[: max(1, query.limit)]
        return [
            Resource(id=str(r["id"]), name=str(r["name"]), attributes={k: v for k, v in r.items()})
            for r in rows
        ]

    async def validate(self, reference: str, required_state: str = "approved") -> ChangeValidation:
        # Simulated rule: references ending in an even digit are "approved".
        ref = (reference or "").strip()
        if not ref:
            return ChangeValidation(
                ok=False, reference=ref, state="missing", reason="No request reference supplied"
            )
        approved = ref[-1].isdigit() and int(ref[-1]) % 2 == 0
        state = "approved" if approved else "pending"
        return ChangeValidation(
            ok=(state == required_state),
            reference=ref,
            state=state,
            reason="" if approved else f"Request {ref} is {state}, requires {required_state}",
        )

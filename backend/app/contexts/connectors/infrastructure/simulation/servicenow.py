"""Simulated ServiceNow connector — CMDB discovery + change/request approval validation."""

from __future__ import annotations

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

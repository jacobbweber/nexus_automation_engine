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

# A small, believable CMDB the discovery adapter filters over.
_CMDB: list[dict[str, object]] = [
    {
        "id": "ci-1001",
        "name": "web-prod-01",
        "fqdn": "web-prod-01.sim.internal",
        "env": "Production",
        "os": "RHEL9",
    },
    {
        "id": "ci-1002",
        "name": "web-prod-02",
        "fqdn": "web-prod-02.sim.internal",
        "env": "Production",
        "os": "RHEL9",
    },
    {
        "id": "ci-1003",
        "name": "app-stg-01",
        "fqdn": "app-stg-01.sim.internal",
        "env": "Staging",
        "os": "RHEL9",
    },
    {
        "id": "ci-1004",
        "name": "db-prod-01",
        "fqdn": "db-prod-01.sim.internal",
        "env": "Production",
        "os": "Windows2022",
    },
    {
        "id": "ci-1005",
        "name": "dev-box-07",
        "fqdn": "dev-box-07.sim.internal",
        "env": "Development",
        "os": "Ubuntu24",
    },
]


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
        rows = [r for r in _CMDB if not env or r.get("env") == env]
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

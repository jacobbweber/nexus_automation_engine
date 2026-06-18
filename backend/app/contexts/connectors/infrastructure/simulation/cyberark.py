"""Simulated CyberArk connector — short-lived credential leasing (memory-only)."""

from __future__ import annotations

from datetime import timedelta

from app.contexts.connectors.domain.models import (
    Capabilities,
    ConnectorAction,
    ConnectorCategory,
    ConnectorKind,
    CredentialLease,
    ParamField,
    SecretRequest,
    _utcnow,
)
from app.shared_kernel.ids import new_id


class CyberArkSimConnector:
    kind = ConnectorKind.CYBERARK

    def capabilities(self) -> Capabilities:
        return Capabilities(
            kind=ConnectorKind.CYBERARK,
            category=ConnectorCategory.SYSTEM_OF_RECORD,
            display_name="CyberArk",
            description="Lease short-lived credentials at execution time (never persisted).",
            streams_logs=False,
            actions=[
                ConnectorAction(
                    name="lease",
                    label="Lease credential",
                    params=[
                        ParamField(name="safe", type="string", label="Safe", required=True),
                        ParamField(
                            name="object_name", type="string", label="Object", required=True
                        ),
                    ],
                )
            ],
        )

    async def lease(self, request: SecretRequest) -> CredentialLease:
        # A real adapter would call the vault; the secret here is ephemeral and fake.
        return CredentialLease(
            lease_id=new_id("lease"),
            username=f"svc_{request.object_name}".lower(),
            secret=new_id("sim-secret"),
            expires_at=_utcnow() + timedelta(minutes=15),
        )

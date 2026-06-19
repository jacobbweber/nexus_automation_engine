"""Simulated VMware (VCF 9) execution connector."""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.contexts.connectors.domain.models import (
    Capabilities,
    ConnectorAction,
    ConnectorCategory,
    ConnectorKind,
    ExecutionRequest,
    LogEvent,
    ParamField,
    StreamType,
)
from app.contexts.connectors.domain.ports import ConnectorError
from app.contexts.connectors.infrastructure.simulation._support import (
    CYAN,
    GREEN,
    YELLOW,
    color,
    jitter,
)


def _line(msg: str, stream: StreamType = StreamType.STDOUT) -> LogEvent:
    return LogEvent(message=msg, stream=stream)


# action -> (label, [stream lines])
_FLOWS: dict[str, tuple[str, list[str]]] = {
    "deploy_workload_domain": (
        "Deploy VCF Workload Domain",
        [
            "Validating SDDC Manager prerequisites...",
            "Commissioning 4 ESXi hosts...",
            "Creating vSphere cluster 'wld-prod-01'...",
            "Deploying NSX-T managers (3)...",
            "Configuring vSAN datastore...",
            "Workload domain 'wld-prod-01' ready.",
        ],
    ),
    "add_esxi_host": (
        "Add ESXi Host to Cluster",
        [
            "Commissioning host esx-09.vcf.local...",
            "Applying host profile...",
            "Entering cluster, migrating vMotion network...",
            "Host added; DRS rebalancing.",
        ],
    ),
    "vmotion": (
        "vMotion VM",
        [
            "Checking compatibility (EVC mode)...",
            "Migrating active memory state...",
            "Switching over...",
            "vMotion complete; 0 ping loss.",
        ],
    ),
    "create_datastore": (
        "Create vVol Datastore",
        [
            "Registering storage provider (VASA)...",
            "Creating vVol datastore 'ds-vvol-02'...",
            "Mounting on 8 hosts...",
            "Datastore online.",
        ],
    ),
    "delete_datastore": (
        "Delete Datastore (CONTROLLED)",
        [
            "Checking for registered VMs...",
            "Unmounting from 8 hosts...",
            "Detaching device...",
            "Datastore deleted.",
        ],
    ),
    "nsx_edge_deploy": (
        "Deploy NSX Edge Cluster",
        [
            "Deploying edge nodes (2) form factor LARGE...",
            "Configuring Tier-0 gateway + BGP...",
            "Edge cluster healthy.",
        ],
    ),
}


class VmwareSimConnector:
    kind = ConnectorKind.VMWARE

    def capabilities(self) -> Capabilities:
        actions = [
            ConnectorAction(
                name=name,
                label=label,
                params=[ParamField(name="target", type="string", label="Target object")],
            )
            for name, (label, _) in _FLOWS.items()
        ]
        return Capabilities(
            kind=ConnectorKind.VMWARE,
            category=ConnectorCategory.EXECUTION,
            display_name="VMware (VCF 9)",
            description="VMware Cloud Foundation lifecycle: domains, hosts, vMotion, storage, NSX.",
            supports_check_mode=True,
            supports_diff=False,
            actions=actions,
        )

    async def execute(self, request: ExecutionRequest) -> AsyncIterator[LogEvent]:
        flow = _FLOWS.get(request.action)
        if flow is None:
            raise ConnectorError(f"VMware: unknown action {request.action!r}")
        label, lines = flow
        mode = " [DRY RUN]" if request.check_mode else ""
        yield _line(color(f"VCF SDDC Manager :: {label}{mode}", CYAN, bold=True))
        await jitter()
        for ln in lines:
            yield _line(color("  • ", YELLOW) + ln)
            await jitter()
            if request.params.get("force_fail"):
                yield _line(color("ERROR: task vim.fault.Timedout", "\033[31m"), StreamType.STDERR)
                raise ConnectorError("VCF task failed (simulated)")
        yield _line(color(f"✓ {label} completed", GREEN, bold=True))

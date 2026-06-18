"""Simulated Terraform execution connector (plan / apply / destroy)."""

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

_RESOURCES = [
    "aws_vpc.main",
    "aws_subnet.private[0]",
    "aws_subnet.private[1]",
    "aws_eks_cluster.this",
    "aws_eks_node_group.workers",
]


def _line(message: str, stream: StreamType = StreamType.STDOUT) -> LogEvent:
    return LogEvent(message=message, stream=stream)


class TerraformSimConnector:
    kind = ConnectorKind.TERRAFORM

    def capabilities(self) -> Capabilities:
        return Capabilities(
            kind=ConnectorKind.TERRAFORM,
            category=ConnectorCategory.EXECUTION,
            display_name="Terraform",
            description="Plan and apply infrastructure-as-code.",
            supports_check_mode=True,  # plan == dry run
            supports_diff=True,
            actions=[
                ConnectorAction(
                    name="plan",
                    label="Plan",
                    params=[
                        ParamField(
                            name="workspace", type="string", label="Workspace", required=True
                        ),
                        ParamField(name="var_file", type="string", label="Var file"),
                    ],
                ),
                ConnectorAction(
                    name="apply",
                    label="Apply",
                    params=[
                        ParamField(
                            name="workspace", type="string", label="Workspace", required=True
                        ),
                        ParamField(name="var_file", type="string", label="Var file"),
                        ParamField(name="auto_approve", type="boolean", label="Auto approve"),
                    ],
                ),
                ConnectorAction(name="destroy", label="Destroy", params=[]),
            ],
        )

    async def execute(self, request: ExecutionRequest) -> AsyncIterator[LogEvent]:
        action = request.action
        if action not in {"plan", "apply", "destroy"}:
            raise ConnectorError(f"Terraform: unknown action {action!r}")
        workspace = request.params.get("workspace", "default")

        yield _line(color(f"Initializing Terraform workspace '{workspace}'...", CYAN))
        await jitter()
        yield _line("Refreshing state... done")
        await jitter()

        if action == "plan" or request.check_mode:
            for r in _RESOURCES:
                yield _line(color(f"  + {r}", GREEN) + " will be created")
                await jitter()
            yield _line(
                color(f"\nPlan: {len(_RESOURCES)} to add, 0 to change, 0 to destroy.", YELLOW)
            )
            return

        if action == "destroy":
            for r in reversed(_RESOURCES):
                yield _line(color(f"  - {r}", "\033[31m") + " destroyed")
                await jitter()
            yield _line(color("\nDestroy complete!", YELLOW))
            return

        # apply
        for r in _RESOURCES:
            yield _line(f"{r}: Creating...")
            await jitter()
            if request.params.get("force_fail") and r.endswith("workers"):
                yield _line(
                    color(f"Error: creation of {r} failed: quota exceeded", "\033[31m"),
                    StreamType.STDERR,
                )
                raise ConnectorError(f"Terraform apply failed on {r} (simulated)")
            yield _line(color(f"{r}: Creation complete", GREEN))
        yield _line(
            color(f"\nApply complete! Resources: {len(_RESOURCES)} added.", GREEN, bold=True)
        )

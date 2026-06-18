"""Simulated script executor connector (PowerShell/Bash over WinRM/SSH jump-box)."""

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
from app.contexts.connectors.infrastructure.simulation._support import GREEN, GREY, color, jitter


def _line(message: str, stream: StreamType = StreamType.STDOUT) -> LogEvent:
    return LogEvent(message=message, stream=stream)


class ScriptSimConnector:
    kind = ConnectorKind.SCRIPT

    def capabilities(self) -> Capabilities:
        return Capabilities(
            kind=ConnectorKind.SCRIPT,
            category=ConnectorCategory.EXECUTION,
            display_name="Script Executor",
            description="Run PowerShell/Bash on a target via WinRM/SSH.",
            supports_check_mode=False,
            supports_diff=False,
            actions=[
                ConnectorAction(
                    name="run",
                    label="Run script",
                    params=[
                        ParamField(
                            name="shell",
                            type="select",
                            label="Shell",
                            choices=["powershell", "bash"],
                            default="powershell",
                        ),
                        ParamField(
                            name="transport",
                            type="select",
                            label="Transport",
                            choices=["winrm", "ssh"],
                            default="winrm",
                        ),
                        ParamField(
                            name="target", type="string", label="Target host", required=True
                        ),
                        ParamField(name="script", type="code", label="Script", required=True),
                    ],
                )
            ],
        )

    async def execute(self, request: ExecutionRequest) -> AsyncIterator[LogEvent]:
        if request.action != "run":
            raise ConnectorError(f"Script: unknown action {request.action!r}")
        target = request.params.get("target", "jumpbox-01.sim.internal")
        transport = request.params.get("transport", "winrm")
        shell = request.params.get("shell", "powershell")
        script = str(request.params.get("script", "")).strip()

        yield _line(color(f"[{transport}] connecting to {target} ...", GREY))
        await jitter()
        yield _line(color("connection established", GREEN))
        yield _line(color(f"$ {shell}", GREY))
        for raw in script.splitlines() or ["<empty script>"]:
            yield _line(f"> {raw}")
            await jitter()

        if request.params.get("force_fail"):
            yield _line(color("ERROR: command exited with code 1", "\033[31m"), StreamType.STDERR)
            raise ConnectorError("Script execution failed (simulated)")

        yield _line(color("OK (exit 0)", GREEN))

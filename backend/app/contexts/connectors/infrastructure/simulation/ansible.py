"""Simulated Ansible (AAP/Controller) execution connector."""

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
    GREEN,
    YELLOW,
    color,
    jitter,
)


def _line(message: str, stream: StreamType = StreamType.STDOUT) -> LogEvent:
    return LogEvent(message=message, stream=stream)


class AnsibleSimConnector:
    kind = ConnectorKind.ANSIBLE

    def capabilities(self) -> Capabilities:
        return Capabilities(
            kind=ConnectorKind.ANSIBLE,
            category=ConnectorCategory.EXECUTION,
            display_name="Ansible (AAP)",
            description="Run playbooks / job templates against managed hosts.",
            supports_check_mode=True,
            supports_diff=True,
            actions=[
                ConnectorAction(
                    name="run_job_template",
                    label="Run playbooks",
                    description="Execute one or more playbooks / a job template.",
                    params=[
                        ParamField(
                            name="playbooks",
                            type="list",
                            label="Playbooks",
                            required=True,
                            help="Playbook files or a job template id.",
                        ),
                        ParamField(
                            name="inventory",
                            type="string",
                            label="Inventory",
                            help="Hosts or a {{cmdb_lookup}} reference.",
                        ),
                        ParamField(name="extra_vars", type="keyvalue", label="Extra vars"),
                    ],
                )
            ],
        )

    async def execute(self, request: ExecutionRequest) -> AsyncIterator[LogEvent]:
        if request.action not in {"run_job_template", "run"}:
            raise ConnectorError(f"Ansible: unknown action {request.action!r}")

        raw_playbooks = request.params.get("playbooks") or ["site.yml"]
        if isinstance(raw_playbooks, str):
            playbooks: list[str] = [raw_playbooks]
        elif isinstance(raw_playbooks, list):
            playbooks = [str(p) for p in raw_playbooks]
        else:
            playbooks = ["site.yml"]
        hosts = _resolve_hosts(request.params.get("inventory"))
        mode = " (CHECK MODE)" if request.check_mode else ""

        yield _line(
            color(f"Running {len(playbooks)} playbook(s) on {len(hosts)} host(s){mode}", YELLOW)
        )
        await jitter()

        for pb in playbooks:
            yield _line(color(f"\nPLAY [{pb}] " + "*" * 50, GREEN))
            await jitter()
            yield _line("TASK [Gathering Facts] " + "*" * 47)
            for h in hosts:
                yield _line(color(f"ok: [{h}]", GREEN))
            await jitter()

            yield _line("TASK [Enforce configuration] " + "*" * 41)
            if request.diff_mode:
                yield _line("--- before\n+++ after\n@@ -1 +1 @@\n-Setting=old\n+Setting=new")
            for h in hosts:
                verb = "changed" if not request.check_mode else "changed (check)"
                yield _line(color(f"{verb}: [{h}]", YELLOW))
            await jitter()

        if request.params.get("force_fail"):
            yield _line(
                color("fatal: task failed on one or more hosts", "\033[31m"), StreamType.STDERR
            )
            raise ConnectorError("Ansible play failed (simulated)")

        yield _line(color("\nPLAY RECAP " + "*" * 60, GREEN))
        for h in hosts:
            yield _line(
                color(f"{h}", GREEN)
                + f" : ok=2    changed={'0' if request.check_mode else '1'}    "
                "unreachable=0    failed=0"
            )


def _resolve_hosts(inventory: object) -> list[str]:
    if isinstance(inventory, list) and inventory:
        out = []
        for item in inventory:
            if isinstance(item, dict):
                out.append(str(item.get("name") or item.get("fqdn") or item.get("id")))
            else:
                out.append(str(item))
        return out
    if isinstance(inventory, str) and inventory and not inventory.startswith("{{"):
        return [h.strip() for h in inventory.split(",") if h.strip()]
    return ["host-01.sim.internal", "host-02.sim.internal"]

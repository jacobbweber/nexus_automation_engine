"""The DAG execution engine — ported from the Ava-POC Foundry, re-homed on Nexus models.

Resolves the graph topologically, runs independent branches concurrently (bounded by a
semaphore), activates children based on condition/switch routing, propagates skips so the graph
never hangs, retries per-node with optional error branches, and persists/streams each step.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from app.contexts.orchestration_canvas.application.node_actions import run_node_action
from app.contexts.orchestration_canvas.domain.models import (
    Edge,
    Node,
    NodeType,
    StepStatus,
    WorkflowStep,
)
from app.contexts.orchestration_canvas.infrastructure.repository import CanvasRepository
from app.shared_kernel.errors import DomainError
from app.shared_kernel.ids import new_id
from app.shared_kernel.variable_pool import VariablePool

WsCallback = Callable[[dict[str, Any]], Any]
_CONCURRENCY = 5


def topological_order(nodes: list[Node], edges: list[Edge]) -> list[str]:
    adj: dict[str, list[str]] = {n.id: [] for n in nodes}
    indeg: dict[str, int] = {n.id: 0 for n in nodes}
    for e in edges:
        if e.source in adj and e.target in adj:
            adj[e.source].append(e.target)
            indeg[e.target] += 1
    queue = [nid for nid, d in indeg.items() if d == 0]
    order: list[str] = []
    while queue:
        u = queue.pop(0)
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    if len(order) != len(nodes):
        raise DomainError("Workflow graph has a cycle — must be a DAG")
    return order


async def execute_graph(
    nodes: list[Node],
    edges: list[Edge],
    pool: VariablePool,
    run_id: str,
    ws: WsCallback | None = None,
    repo: CanvasRepository | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    order = topological_order(nodes, edges)
    node_map = {n.id: n for n in nodes}
    outputs: dict[str, dict[str, Any]] = {}
    states: dict[str, StepStatus] = {n.id: StepStatus.PENDING for n in nodes}
    errors: dict[str, str] = {}

    incoming: dict[str, list[Edge]] = {n.id: [] for n in nodes}
    outgoing: dict[str, list[Edge]] = {n.id: [] for n in nodes}
    for e in edges:
        if e.source in outgoing:
            outgoing[e.source].append(e)
        if e.target in incoming:
            incoming[e.target].append(e)

    semaphore = asyncio.Semaphore(_CONCURRENCY)
    tasks: dict[str, asyncio.Task] = {}

    async def emit(event: dict[str, Any]) -> None:
        if ws:
            await ws(event)

    def _save(
        step_status: StepStatus,
        node: Node,
        *,
        started: datetime,
        out: dict | None = None,
        err: str | None = None,
        retries: int = 0,
    ) -> None:
        if persist and repo is not None:
            repo.save_step(
                WorkflowStep(
                    step_id=new_id("step"),
                    run_id=run_id,
                    node_id=node.id,
                    node_type=str(node.type),
                    status=step_status,
                    started_at=started,
                    completed_at=datetime.now(UTC) if step_status != StepStatus.RUNNING else None,
                    inputs=node.data,
                    outputs=out or {},
                    error_message=err,
                    retry_count=retries,
                )
            )

    def _is_active(node_id: str, parent_results: dict[str, tuple[StepStatus, Edge]]) -> bool:
        if not incoming[node_id]:
            return True
        for parent_id, (status, edge) in parent_results.items():
            if status != StepStatus.COMPLETED:
                continue
            parent = node_map[parent_id]
            if parent.type == NodeType.CONDITION:
                expected = "true" if outputs[parent_id].get("result") else "false"
                if edge.sourceHandle == expected:
                    return True
            elif parent.type == NodeType.SWITCH_ROUTER:
                value = str(outputs[parent_id].get("result", ""))
                handle = None
                for case in parent.data.get("cases", []):
                    if str(case.get("value")) == value:
                        handle = case.get("target_handle")
                        break
                handle = handle or parent.data.get("default_handle", "case_default")
                if edge.sourceHandle == handle:
                    return True
            else:
                return True
        return False

    async def run_node(node_id: str) -> StepStatus:
        node = node_map[node_id]
        parent_results: dict[str, tuple[StepStatus, Edge]] = {}
        for edge in incoming[node_id]:
            parent_results[edge.source] = (await tasks[edge.source], edge)

        if not _is_active(node_id, parent_results):
            states[node_id] = StepStatus.SKIPPED
            await emit({"type": "step", "node_id": node_id, "status": "skipped"})
            _save(StepStatus.SKIPPED, node, started=datetime.now(UTC))
            return StepStatus.SKIPPED

        states[node_id] = StepStatus.RUNNING
        await emit(
            {"type": "step", "node_id": node_id, "status": "running", "node_type": str(node.type)}
        )

        max_retries = int(node.data.get("max_retries", 0))
        retry_delay = float(node.data.get("retry_delay_seconds", 0.5))
        timeout = float(node.data.get("timeout_seconds", 120))

        attempt = 0
        last_err = ""
        while attempt <= max_retries:
            started = datetime.now(UTC)
            try:
                async with semaphore:
                    result = await asyncio.wait_for(
                        run_node_action(node, pool, run_id, ws), timeout=timeout
                    )
                outputs[node_id] = result
                pool.set(node_id, result)
                states[node_id] = StepStatus.COMPLETED
                await emit(
                    {"type": "step", "node_id": node_id, "status": "completed", "outputs": result}
                )
                _save(StepStatus.COMPLETED, node, started=started, out=result, retries=attempt)
                return StepStatus.COMPLETED
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                attempt += 1
                if attempt <= max_retries:
                    await asyncio.sleep(retry_delay)

        states[node_id] = StepStatus.FAILED
        errors[node_id] = last_err
        await emit({"type": "step", "node_id": node_id, "status": "failed", "error": last_err})
        _save(StepStatus.FAILED, node, started=datetime.now(UTC), err=last_err, retries=max_retries)

        # Error branch: if an outgoing "error" edge exists, continue down it.
        if any(e.sourceHandle == "error" for e in outgoing[node_id]):
            outputs[node_id] = {"error": last_err}
            pool.set(node_id, {"error": last_err})
            return StepStatus.COMPLETED
        raise DomainError(f"Node {node_id} failed: {last_err}")

    async def run_node_safe(node_id: str) -> StepStatus:
        try:
            return await run_node(node_id)
        except Exception as exc:  # noqa: BLE001
            states[node_id] = StepStatus.FAILED
            errors[node_id] = str(exc)
            return StepStatus.FAILED

    for node_id in order:
        tasks[node_id] = asyncio.create_task(run_node_safe(node_id))
    await asyncio.gather(*tasks.values(), return_exceptions=True)

    failed = [nid for nid, task in tasks.items() if task.result() == StepStatus.FAILED]
    if failed:
        with contextlib.suppress(Exception):
            await emit({"type": "run_failed", "run_id": run_id})
        raise DomainError("; ".join(f"{nid}: {errors.get(nid, 'failed')}" for nid in failed))

    end_nodes = [n.id for n in nodes if n.type == NodeType.END]
    if end_nodes and end_nodes[0] in outputs:
        return outputs[end_nodes[0]]
    return outputs

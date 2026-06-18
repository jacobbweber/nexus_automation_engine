"""Engine mechanics: linear runs, condition skip, error branch, cycles, approval gates."""

from __future__ import annotations

import asyncio

import pytest
from app.contexts.orchestration_canvas.application.engine import execute_graph
from app.contexts.orchestration_canvas.application.node_actions import (
    pending_approvals,
    resolve_approval,
)
from app.contexts.orchestration_canvas.domain.models import Edge, Node, NodeType
from app.shared_kernel.errors import DomainError
from app.shared_kernel.variable_pool import VariablePool


def _pool(inputs=None) -> VariablePool:
    p = VariablePool()
    p.set("start", inputs or {})
    return p


async def _run(nodes, edges, inputs=None, run_id="r"):
    return await execute_graph(nodes, edges, _pool(inputs), run_id, persist=False)


async def test_linear_run_reaches_end():
    nodes = [
        Node(id="start", type=NodeType.START),
        Node(
            id="task",
            type=NodeType.AUTOMATION_TASK,
            data={"connector": "terraform", "action": "plan", "params": {"workspace": "p"}},
        ),
        Node(id="end", type=NodeType.END, data={"outputs": {"ok": "{{task.completed}}"}}),
    ]
    edges = [Edge(source="start", target="task"), Edge(source="task", target="end")]
    out = await _run(nodes, edges)
    assert out["ok"] is True


async def test_condition_skips_false_branch():
    nodes = [
        Node(id="start", type=NodeType.START),
        Node(
            id="cond",
            type=NodeType.CONDITION,
            data={"variable": "{{start.n}}", "operator": ">", "value": "5"},
        ),
        Node(
            id="A",
            type=NodeType.VARIABLE_ASSIGNER,
            data={"assignments": [{"key": "branch", "value": "A"}]},
        ),
        Node(
            id="B",
            type=NodeType.VARIABLE_ASSIGNER,
            data={"assignments": [{"key": "branch", "value": "B"}]},
        ),
        Node(id="end", type=NodeType.END, data={"outputs": {"branch": "{{branch}}"}}),
    ]
    edges = [
        Edge(source="start", target="cond"),
        Edge(source="cond", target="A", sourceHandle="true"),
        Edge(source="cond", target="B", sourceHandle="false"),
        Edge(source="A", target="end"),
        Edge(source="B", target="end"),
    ]
    out = await _run(nodes, edges, inputs={"n": 10})
    assert out["branch"] == "A"


async def test_error_branch_allows_recovery():
    nodes = [
        Node(id="start", type=NodeType.START),
        Node(
            id="task",
            type=NodeType.AUTOMATION_TASK,
            data={
                "connector": "terraform",
                "action": "apply",
                "params": {"workspace": "p", "force_fail": True},
            },
        ),
        Node(
            id="recover",
            type=NodeType.VARIABLE_ASSIGNER,
            data={"assignments": [{"key": "recovered", "value": "yes"}]},
        ),
        Node(id="end", type=NodeType.END, data={"outputs": {"recovered": "{{recovered}}"}}),
    ]
    edges = [
        Edge(source="start", target="task"),
        Edge(source="task", target="recover", sourceHandle="error"),
        Edge(source="recover", target="end"),
    ]
    out = await _run(nodes, edges)
    assert out["recovered"] == "yes"


async def test_failure_without_error_branch_raises():
    nodes = [
        Node(id="start", type=NodeType.START),
        Node(
            id="task",
            type=NodeType.AUTOMATION_TASK,
            data={
                "connector": "terraform",
                "action": "apply",
                "params": {"workspace": "p", "force_fail": True},
            },
        ),
        Node(id="end", type=NodeType.END),
    ]
    edges = [Edge(source="start", target="task"), Edge(source="task", target="end")]
    with pytest.raises(DomainError):
        await _run(nodes, edges)


async def test_cycle_detection():
    nodes = [Node(id="a", type=NodeType.DELAY), Node(id="b", type=NodeType.DELAY)]
    edges = [Edge(source="a", target="b"), Edge(source="b", target="a")]
    with pytest.raises(DomainError):
        await _run(nodes, edges)


async def test_approval_gate_pauses_and_resumes():
    nodes = [
        Node(id="start", type=NodeType.START),
        Node(id="gate", type=NodeType.APPROVAL_GATE, data={"message": "ok?"}),
        Node(id="end", type=NodeType.END, data={"outputs": {"approved": "{{gate.approved}}"}}),
    ]
    edges = [Edge(source="start", target="gate"), Edge(source="gate", target="end")]
    run_id = "approval-run"
    task = asyncio.create_task(_run(nodes, edges, run_id=run_id))

    for _ in range(200):
        if pending_approvals.get(run_id, {}).get("gate"):
            break
        await asyncio.sleep(0.01)
    assert resolve_approval(run_id, "gate", approved=True)

    out = await task
    assert out["approved"] is True


async def test_canonical_terraform_to_ansible_pattern():
    """Terraform plan -> CMDB lookup -> Ansible run, using CMDB output as inventory."""
    nodes = [
        Node(id="start", type=NodeType.START),
        Node(
            id="tf",
            type=NodeType.AUTOMATION_TASK,
            data={"connector": "terraform", "action": "plan", "params": {"workspace": "p"}},
        ),
        Node(
            id="cmdb",
            type=NodeType.CMDB_LOOKUP,
            data={"table": "cmdb_ci_server", "filters": {"env": "Production"}},
        ),
        Node(
            id="ans",
            type=NodeType.AUTOMATION_TASK,
            data={
                "connector": "ansible",
                "action": "run_job_template",
                "params": {"playbooks": ["site.yml"], "inventory": "{{cmdb.result}}"},
            },
        ),
        Node(
            id="end",
            type=NodeType.END,
            data={"outputs": {"hosts": "{{cmdb.count}}", "ansible_ok": "{{ans.completed}}"}},
        ),
    ]
    edges = [
        Edge(source="start", target="tf"),
        Edge(source="tf", target="cmdb"),
        Edge(source="cmdb", target="ans"),
        Edge(source="ans", target="end"),
    ]
    out = await _run(nodes, edges)
    assert out["ansible_ok"] is True
    assert out["hosts"] >= 1

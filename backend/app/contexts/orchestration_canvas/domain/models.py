"""Canvas domain models: the workflow graph, runs, and steps."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(StrEnum):
    # Control / data flow (generic)
    START = "start"
    END = "end"
    CONDITION = "condition"
    SWITCH_ROUTER = "switch_router"
    DELAY = "delay"
    VARIABLE_ASSIGNER = "variable_assigner"
    TEMPLATE_TRANSFORM = "template_transform"
    HTTP_REQUEST = "http_request"
    SUB_WORKFLOW = "sub_workflow"
    # Backend-integration (the Nexus re-targeting)
    AUTOMATION_TASK = "automation_task"
    CMDB_LOOKUP = "cmdb_lookup"
    REQUEST_VALIDATION = "request_validation"
    SECRET_LEASE = "secret_lease"
    TELEMETRY_PROBE = "telemetry_probe"
    APPROVAL_GATE = "approval_gate"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Node(BaseModel):
    id: str
    type: NodeType
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    data: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    id: str | None = None
    source: str
    target: str
    sourceHandle: str | None = None  # noqa: N815 - matches canvas JSON shape
    targetHandle: str | None = None  # noqa: N815


class WorkflowGraph(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    viewport: dict[str, float] = Field(default_factory=dict)


class Workflow(BaseModel):
    id: str
    name: str
    description: str = ""
    graph: WorkflowGraph = Field(default_factory=WorkflowGraph)
    created_at: datetime
    updated_at: datetime


class WorkflowStep(BaseModel):
    step_id: str
    run_id: str
    node_id: str
    node_type: str
    status: StepStatus
    started_at: datetime
    completed_at: datetime | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    retry_count: int = 0


class WorkflowRun(BaseModel):
    run_id: str
    workflow_id: str
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    steps: list[WorkflowStep] = Field(default_factory=list)


class WorkflowVersion(BaseModel):
    version_id: str
    workflow_id: str
    graph: WorkflowGraph
    description: str = ""
    created_at: datetime

"""Canvas REST + WebSocket routes."""

from __future__ import annotations

import contextlib

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.contexts.identity_access.api.deps import get_current_user, require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.contexts.orchestration_canvas.application.broker import get_run_broker
from app.contexts.orchestration_canvas.application.service import CanvasService
from app.contexts.orchestration_canvas.domain.models import (
    ReviewRecord,
    Workflow,
    WorkflowGraph,
    WorkflowRun,
    WorkflowVersion,
)

router = APIRouter(prefix="/canvas", tags=["canvas"])


class SaveWorkflowRequest(BaseModel):
    id: str | None = None
    name: str
    description: str = ""
    graph: WorkflowGraph = Field(default_factory=WorkflowGraph)


@router.get("/workflows", response_model=list[Workflow])
def list_workflows() -> list[Workflow]:
    return CanvasService().list_workflows()


@router.get("/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: str) -> Workflow:
    return CanvasService().get_workflow(workflow_id)


@router.post("/workflows", response_model=Workflow)
def save_workflow(body: SaveWorkflowRequest) -> Workflow:
    return CanvasService().save_workflow(
        name=body.name, graph=body.graph, description=body.description, workflow_id=body.id
    )


@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: str) -> dict[str, str]:
    CanvasService().delete_workflow(workflow_id)
    return {"status": "deleted"}


class RunRequest(BaseModel):
    inputs: dict[str, object] = Field(default_factory=dict)


class RunResponse(BaseModel):
    run_id: str


@router.post("/workflows/{workflow_id}/run", response_model=RunResponse)
async def run_workflow(
    workflow_id: str, body: RunRequest, _user: UserContext = Depends(get_current_user)
) -> RunResponse:
    # async so asyncio.create_task in start_run has a running event loop. Auth: security audit S1.
    run_id = CanvasService().start_run(workflow_id, body.inputs)
    return RunResponse(run_id=run_id)


@router.get("/workflows/{workflow_id}/runs", response_model=list[WorkflowRun])
def list_runs(workflow_id: str) -> list[WorkflowRun]:
    return CanvasService().list_runs(workflow_id)


@router.get("/runs/{run_id}", response_model=WorkflowRun)
def get_run(run_id: str) -> WorkflowRun:
    return CanvasService().get_run(run_id)


@router.get("/workflows/{workflow_id}/versions", response_model=list[WorkflowVersion])
def list_versions(workflow_id: str) -> list[WorkflowVersion]:
    return CanvasService().list_versions(workflow_id)


@router.post("/workflows/{workflow_id}/versions", response_model=WorkflowVersion)
def snapshot_version(workflow_id: str, description: str = "") -> WorkflowVersion:
    return CanvasService().snapshot_version(workflow_id, description)


@router.post("/workflows/{workflow_id}/submit", response_model=Workflow)
def submit_for_review(workflow_id: str, user: UserContext = Depends(get_current_user)) -> Workflow:
    return CanvasService().submit_for_review(workflow_id, submitted_by=user.username)


class ReviewDecision(BaseModel):
    decision: str  # approve | request_changes | reject | publish
    comment: str = ""


@router.post("/workflows/{workflow_id}/review", response_model=Workflow)
def review_workflow(
    workflow_id: str,
    body: ReviewDecision,
    reviewer: UserContext = Depends(require_role(GlobalRole.ENGINEER)),
) -> Workflow:
    return CanvasService().review(workflow_id, body.decision, reviewer.username, body.comment)


@router.get("/reviews/pending", response_model=list[Workflow])
def pending_reviews(
    _reviewer: UserContext = Depends(require_role(GlobalRole.ENGINEER)),
) -> list[Workflow]:
    return CanvasService().pending_reviews()


@router.get("/workflows/{workflow_id}/reviews", response_model=list[ReviewRecord])
def workflow_reviews(workflow_id: str) -> list[ReviewRecord]:
    return CanvasService().reviews(workflow_id)


class ApprovalResolution(BaseModel):
    run_id: str
    node_id: str
    approved: bool
    response: str = ""


@router.post("/approvals/resolve")
def resolve_approval(body: ApprovalResolution) -> dict[str, bool]:
    ok = CanvasService().resume_approval(body.run_id, body.node_id, body.approved, body.response)
    return {"resolved": ok}


def _ws_authenticated(websocket: WebSocket) -> bool:
    import jwt as _jwt

    from app.contexts.identity_access.application.security import decode_token

    token = websocket.query_params.get("token", "")
    if not token:
        return False
    try:
        decode_token(token)
        return True
    except _jwt.PyJWTError:
        return False


@router.websocket("/runs/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    if not _ws_authenticated(websocket):
        await websocket.send_json({"type": "error", "detail": "unauthorized"})
        await websocket.close(code=1008)
        return
    broker = get_run_broker()
    queue = broker.subscribe(run_id)
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        broker.unsubscribe(run_id, queue)
        with contextlib.suppress(Exception):
            await websocket.close()

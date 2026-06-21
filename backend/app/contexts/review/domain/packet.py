"""The Change Review Packet — a deterministic, multi-audience rendering of what a run will do.

Composed (no AI, ADR-0008) from the workflow graph + each building block's authored plain summary:
- **technical**: per automation step — connector, action, resolved params, idempotency.
- **narrative** (non-technical / executive): plain-language steps in order + outcome/rollback.
- **flowchart**: a human-labelled phase list (LogicFlow shape).
Plus the change classification headline (26.2).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.contexts.review.domain.classification import (
    ChangeClass,
    ChangeContext,
    ReviewerLevel,
    ReviewPolicy,
    assess,
)
from app.shared_kernel.idempotency import IdempotencyClass, infer_idempotency

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_TARGET_KEYS = ("target", "inventory", "object", "name", "workspace")


class TechnicalStep(BaseModel):
    node_id: str
    name: str
    connector: str
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    idempotency: str = "idempotent"


class NarrativeStep(BaseModel):
    step: int
    text: str


class FlowPhase(BaseModel):
    label: str
    kind: str = "action"  # start | action | gate | end


class BlockInfo(BaseModel):
    """The slice of a catalog template the packet builder needs (passed in by the app service)."""

    plain_action: str = ""
    plain_outcome: str = ""
    rollback: str = ""
    risk: str = "low"
    idempotency: IdempotencyClass = IdempotencyClass.IDEMPOTENT


class ReviewPacket(BaseModel):
    workflow_id: str
    workflow_name: str
    change_class: ChangeClass
    required_level: ReviewerLevel
    requires_approval: bool
    reasons: list[str] = Field(default_factory=list)
    risk: str = "low"
    blast_radius: int = 0
    technical: list[TechnicalStep] = Field(default_factory=list)
    narrative: list[NarrativeStep] = Field(default_factory=list)
    flowchart: list[FlowPhase] = Field(default_factory=list)
    summary: str = ""
    rollback: str = ""


def _target_of(params: dict[str, Any]) -> str | None:
    for k in _TARGET_KEYS:
        v = params.get(k)
        if v:
            return str(v)
    return None


def build_packet(
    *,
    workflow_id: str,
    workflow_name: str,
    nodes: list[dict[str, Any]],
    inputs: dict[str, Any] | None = None,
    block_lookup: dict[tuple[str, str], BlockInfo] | None = None,
    policy: ReviewPolicy | None = None,
) -> ReviewPacket:
    """Build a multi-audience review packet from a workflow's nodes.

    ``nodes`` is a list of {id, type, name, connector, action, params}. ``block_lookup`` maps
    (connector, action) -> BlockInfo (authored plain summary + risk + idempotency).
    """
    inputs = inputs or {}
    block_lookup = block_lookup or {}

    technical: list[TechnicalStep] = []
    narrative: list[NarrativeStep] = []
    flow: list[FlowPhase] = [FlowPhase(label="Start", kind="start")]

    targets: set[str] = set()
    max_risk = 0
    worst_idem = IdempotencyClass.IDEMPOTENT
    rollbacks: list[str] = []
    step_no = 0

    for n in nodes:
        ntype = str(n.get("type", ""))
        if ntype in ("human_input", "approval_gate"):
            flow.append(FlowPhase(label="Human approval", kind="gate"))
            continue
        if ntype != "automation_task":
            continue
        connector = str(n.get("connector") or n.get("data", {}).get("connector") or "")
        action = str(n.get("action") or n.get("data", {}).get("action") or "")
        params = n.get("params") or n.get("data", {}).get("params") or {}
        if not isinstance(params, dict):
            params = {}
        if not connector or not action:
            continue
        # Prefer the authored catalog metadata; otherwise infer safely from the action name so a
        # workflow whose node doesn't 1:1 match a catalog block is still classified honestly (a
        # destructive step must not look low-risk just because there's no exact catalog match).
        info = block_lookup.get((connector, action))
        if info is None:
            inferred = infer_idempotency(action)
            destructive = inferred == IdempotencyClass.NON_IDEMPOTENT
            info = BlockInfo(
                idempotency=inferred,
                risk="high" if destructive else "low",
                rollback="restore from snapshot/backup." if destructive else "",
            )
        step_no += 1

        technical.append(
            TechnicalStep(
                node_id=str(n.get("id", "")),
                name=str(n.get("name") or n.get("data", {}).get("name") or action),
                connector=connector,
                action=action,
                params=params,
                idempotency=str(info.idempotency),
            )
        )

        # plain-language step (exec/non-technical): prefer the authored summary
        action_text = info.plain_action or action.replace("_", " ")
        outcome_text = info.plain_outcome or "the resource reaches its desired state"
        narrative.append(NarrativeStep(step=step_no, text=f"{action_text} → {outcome_text}"))
        flow.append(FlowPhase(label=action_text.rstrip("."), kind="action"))

        t = _target_of(params)
        if t:
            targets.add(t)
        max_risk = max(max_risk, _RISK_ORDER.get(info.risk.lower(), 0))
        if info.idempotency == IdempotencyClass.NON_IDEMPOTENT:
            worst_idem = IdempotencyClass.NON_IDEMPOTENT
        if info.rollback:
            rollbacks.append(info.rollback)

    flow.append(FlowPhase(label="Complete", kind="end"))

    risk_name = next((k for k, v in _RISK_ORDER.items() if v == max_risk), "low")
    blast_radius = len(targets)
    prod = any("prod" in t.lower() for t in targets)
    classification = assess(
        ChangeContext(risk=risk_name, blast_radius=blast_radius, prod=prod, idempotency=worst_idem),
        policy,
    )

    summary = (
        "This change will: " + "; ".join(s.text for s in narrative)
        if narrative
        else ("This workflow performs no mutating automation steps.")
    )

    return ReviewPacket(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        change_class=classification.change_class,
        required_level=classification.required_level,
        requires_approval=classification.requires_approval,
        reasons=classification.reasons,
        risk=risk_name,
        blast_radius=blast_radius,
        technical=technical,
        narrative=narrative,
        flowchart=flow,
        summary=summary,
        rollback="; ".join(dict.fromkeys(rollbacks)),
    )

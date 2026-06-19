"""Per-node execution — the heart of "each canvas node binds to a backend".

Each node type resolves its parameters through the VariablePool and (for backend-integration
nodes) acts through the connector ports, so a node never knows whether it's talking to a real or
simulated backend. Human/approval gates pause via a pending-future registry resolved by the
service's resume endpoint.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import httpx
import jinja2

from app.contexts.connectors.domain.models import (
    ConnectorKind,
    DiscoveryQuery,
    ExecutionRequest,
    SecretRequest,
)
from app.contexts.connectors.domain.ports import ConnectorError
from app.contexts.connectors.infrastructure.registry import get_registry
from app.contexts.orchestration_canvas.domain.models import Node, NodeType
from app.shared_kernel.variable_pool import VariablePool

# run_id -> node_id -> Future[{"approved": bool, "response": str}]
pending_approvals: dict[str, dict[str, asyncio.Future]] = {}

WsCallback = Callable[[dict[str, Any]], Any]

_CONTROL_KEYS = {
    "name",
    "connector",
    "action",
    "check_mode",
    "diff_mode",
    "max_retries",
    "retry_delay_seconds",
    "timeout_seconds",
    "params",
}


def resolve_approval(run_id: str, node_id: str, approved: bool, response: str = "") -> bool:
    bucket = pending_approvals.get(run_id, {})
    fut = bucket.get(node_id)
    if fut is not None and not fut.done():
        fut.set_result({"approved": approved, "response": response})
        return True
    return False


def _task_params(data: dict[str, Any], pool: VariablePool) -> dict[str, Any]:
    inline = {k: v for k, v in data.items() if k not in _CONTROL_KEYS}
    params = {**inline, **data.get("params", {})}
    return pool.resolve(params)


async def run_node_action(
    node: Node, pool: VariablePool, run_id: str, ws: WsCallback | None = None
) -> dict[str, Any]:
    data = node.data
    t = node.type

    if t == NodeType.START:
        # Return the run inputs unchanged so the engine's ``pool[node_id] = output`` does not
        # clobber the seeded ``start`` inputs that ``{{start.*}}`` references depend on.
        return pool.pool.get("start", {})

    if t == NodeType.END:
        return pool.resolve(data.get("outputs", {}))

    if t == NodeType.CONDITION:
        a = pool.resolve(data.get("variable", ""))
        b = pool.resolve(data.get("value", ""))
        op = data.get("operator", "==")
        return {"result": _compare(a, b, op, bool(data.get("case_sensitive", True)))}

    if t == NodeType.SWITCH_ROUTER:
        return {"result": pool.resolve(data.get("variable", ""))}

    if t == NodeType.DELAY:
        await asyncio.sleep(float(data.get("delay_seconds", 0)))
        return {"delayed": True}

    if t == NodeType.VARIABLE_ASSIGNER:
        for assignment in data.get("assignments", []):
            pool.set(assignment["key"], pool.resolve(assignment.get("value", "")))
        return {"assigned": True}

    if t == NodeType.TEMPLATE_TRANSFORM:
        env = jinja2.Environment(autoescape=False, undefined=jinja2.ChainableUndefined)
        template = env.from_string(data.get("template", ""))
        return {"result": template.render(**pool.resolve(data.get("variables", {})))}

    if t == NodeType.HTTP_REQUEST:
        return await _http_request(data, pool)

    if t == NodeType.SUB_WORKFLOW:
        from app.contexts.orchestration_canvas.application.service import CanvasService

        sub_inputs = pool.resolve(data.get("inputs", {}))
        run = await CanvasService().run_workflow(data.get("workflow_id", ""), sub_inputs)
        return {"run_id": run.run_id, "status": str(run.status), "outputs": run.outputs}

    if t == NodeType.AUTOMATION_TASK:
        return await _automation_task(data, pool, run_id, ws)

    if t == NodeType.CMDB_LOOKUP:
        return await _cmdb_lookup(data, pool)

    if t == NodeType.REQUEST_VALIDATION:
        ref = str(pool.resolve(data.get("ritm") or data.get("reference", "")))
        required = data.get("required_state", "approved")
        result = await get_registry().approval(ConnectorKind.SERVICENOW).validate(ref, required)
        if not result.ok:
            raise ConnectorError(f"Change not approved: {result.reason or result.state}")
        return result.model_dump(mode="json")

    if t == NodeType.SECRET_LEASE:
        return await _secret_lease(data, pool)

    if t == NodeType.TELEMETRY_PROBE:
        entity = str(pool.resolve(data.get("entity", "")))
        seconds = int(data.get("seconds", 60))
        series = await get_registry().telemetry(ConnectorKind.DYNATRACE).series(entity, seconds)
        peak = max((s.cpu_percent for s in series.samples), default=0)
        return {"sample_count": len(series.samples), "peak_cpu": peak}

    if t in (NodeType.APPROVAL_GATE,):
        return await _approval_gate(node, pool, run_id, ws)

    raise ConnectorError(f"Unsupported node type: {t}")


def _compare(a: Any, b: Any, op: str, case_sensitive: bool = True) -> bool:
    """Rich condition evaluation supporting numeric, string, regex, and list operators."""
    import re

    # Unary operators first.
    if op == "is_empty":
        return a is None or a == "" or a == [] or a == {}
    if op == "is_not_empty":
        return not (a is None or a == "" or a == [] or a == {})

    # Numeric comparison operators.
    if op in (">", ">=", "<", "<="):
        try:
            fa, fb = float(a), float(b)
        except (TypeError, ValueError):
            return False
        return {">": fa > fb, ">=": fa >= fb, "<": fa < fb, "<=": fa <= fb}[op]

    sa, sb = str(a), str(b)
    if not case_sensitive:
        sa, sb = sa.lower(), sb.lower()

    if op == "==":
        return sa == sb
    if op == "!=":
        return sa != sb
    if op == "contains":
        return sb in sa
    if op == "not_contains":
        return sb not in sa
    if op == "starts_with":
        return sa.startswith(sb)
    if op == "ends_with":
        return sa.endswith(sb)
    if op == "matches_regex":
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.search(sb, sa, flags) is not None
    if op == "in_list":
        items = [x.strip() for x in sb.split(",")]
        return sa in items
    return False


def _ssrf_guard(url: str) -> None:
    """Block requests to loopback/private/link-local/metadata hosts (audit S3)."""
    import ipaddress
    import socket
    from urllib.parse import urlparse

    from app.platform.config import get_settings

    if get_settings().http_allow_private:
        return
    host = urlparse(url).hostname
    if not host:
        raise ConnectorError("http_request: invalid URL (no host)")
    if host in {"localhost", "metadata.google.internal", "metadata"}:
        raise ConnectorError(f"http_request: blocked host '{host}' (SSRF policy)")

    candidates: list[str] = []
    try:
        candidates = [host] if ipaddress.ip_address(host) else []
    except ValueError:
        try:
            candidates = [str(info[4][0]) for info in socket.getaddrinfo(host, None)]
        except OSError:
            return  # unresolvable — let the request fail naturally
    for addr in candidates:
        ip = ipaddress.ip_address(addr)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ConnectorError(f"http_request: blocked address {addr} (SSRF policy)")


async def _http_request(data: dict[str, Any], pool: VariablePool) -> dict[str, Any]:
    method = str(data.get("method", "GET")).upper()
    url = str(pool.resolve(data.get("url", "")))
    _ssrf_guard(url)
    headers = pool.resolve(data.get("headers", {})) or {}
    body = pool.resolve(data.get("body", "")) or None
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, headers=headers, content=body)
    try:
        payload = resp.json()
    except Exception:  # noqa: BLE001
        payload = None
    return {"status_code": resp.status_code, "text": resp.text, "json": payload}


async def _automation_task(
    data: dict[str, Any], pool: VariablePool, run_id: str, ws: WsCallback | None
) -> dict[str, Any]:
    kind = ConnectorKind(str(data.get("connector", "")))
    params = _task_params(data, pool)
    # Origin-story validation (3.0): gate in-graph tasks that target a single named CI.
    from app.platform.config import get_settings

    if get_settings().enforce_lifecycle_validation:
        target = params.get("target")
        if isinstance(target, str) and target and not target.startswith("{{"):
            from app.contexts.lifecycle_validation.application.service import ValidationService
            from app.contexts.lifecycle_validation.domain.models import AutomationMeta

            meta = AutomationMeta(
                name=str(data.get("name", kind.value)), action=str(data.get("action", ""))
            )
            await ValidationService().enforce_cmdb_only(meta, target)

    request = ExecutionRequest(
        kind=kind,
        action=str(data.get("action", "")),
        params=params,
        check_mode=bool(data.get("check_mode", False)),
        diff_mode=bool(data.get("diff_mode", False)),
        run_id=run_id,
    )
    connector = get_registry().execution(kind)
    tail: list[str] = []
    count = 0
    async for event in connector.execute(request):
        count += 1
        tail.append(event.message)
        tail = tail[-5:]
        if ws:
            await ws(
                {"type": "node_log", "node": data.get("name", kind.value), "message": event.message}
            )
    return {"completed": True, "line_count": count, "tail": tail}


async def _cmdb_lookup(data: dict[str, Any], pool: VariablePool) -> dict[str, Any]:
    query = DiscoveryQuery(
        source=str(data.get("table", "cmdb_ci_server")),
        filters=pool.resolve(data.get("filters", {})) or {},
        limit=int(data.get("limit", 50)),
    )
    resources = await get_registry().discovery(ConnectorKind.SERVICENOW).discover(query)
    return {"result": [r.model_dump(mode="json") for r in resources], "count": len(resources)}


async def _secret_lease(data: dict[str, Any], pool: VariablePool) -> dict[str, Any]:
    lease = (
        await get_registry()
        .secret_lease(ConnectorKind.CYBERARK)
        .lease(
            SecretRequest(
                safe=str(pool.resolve(data.get("safe", ""))),
                object_name=str(pool.resolve(data.get("object_name", ""))),
            )
        )
    )
    bind_as = data.get("bind_as", "credential")
    # Real secret goes into the pool for downstream nodes; persisted output is masked.
    pool.set(bind_as, {"username": lease.username, "secret": lease.secret})
    return {
        "lease_id": lease.lease_id,
        "username": lease.username,
        "secret": "***masked***",
        "expires_at": lease.expires_at.isoformat(),
    }


async def _approval_gate(
    node: Node, pool: VariablePool, run_id: str, ws: WsCallback | None
) -> dict[str, Any]:
    data = node.data
    message = str(pool.resolve(data.get("message", "Approval required")))
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    pending_approvals.setdefault(run_id, {})[node.id] = fut

    if ws:
        await ws(
            {
                "type": "approval_required",
                "run_id": run_id,
                "node_id": node.id,
                "message": message,
                "approver_roles": data.get("approver_roles", []),
                "require_text_response": data.get("require_text_response", False),
            }
        )
    try:
        timeout = float(data.get("timeout_seconds", 300))
        result = await asyncio.wait_for(fut, timeout=timeout)
        if not result.get("approved"):
            raise ConnectorError("Workflow rejected at approval gate")
        return {"approved": True, "response": result.get("response", "")}
    finally:
        pending_approvals.get(run_id, {}).pop(node.id, None)

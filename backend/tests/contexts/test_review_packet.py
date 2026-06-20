"""Review Packet builder: deterministic multi-audience rendering (story 26.3)."""

from __future__ import annotations

import pytest
from app.contexts.review.domain.packet import BlockInfo, build_packet
from app.shared_kernel.idempotency import IdempotencyClass


def _nodes():
    return [
        {"id": "start", "type": "start", "data": {}},
        {
            "id": "snap",
            "type": "automation_task",
            "data": {
                "connector": "cohesity",
                "action": "run_protection_job",
                "params": {"target": "web-prod-01"},
                "name": "Snapshot",
            },
        },
        {"id": "approve", "type": "approval_gate", "data": {}},
        {
            "id": "patch",
            "type": "automation_task",
            "data": {
                "connector": "ansible",
                "action": "rolling_os_patching",
                "params": {"target": "web-prod-01"},
            },
        },
        {"id": "end", "type": "end", "data": {}},
    ]


def _lookup():
    return {
        ("cohesity", "run_protection_job"): BlockInfo(
            plain_action="Take a backup snapshot",
            plain_outcome="a recovery point exists",
            rollback="discard the snapshot",
            risk="low",
        ),
        ("ansible", "rolling_os_patching"): BlockInfo(
            plain_action="Apply OS patches",
            plain_outcome="hosts are patched and verified",
            rollback="restore from snapshot",
            risk="medium",
            idempotency=IdempotencyClass.IDEMPOTENT,
        ),
    }


def test_packet_has_three_audiences_and_flow():
    p = build_packet(
        workflow_id="wf1",
        workflow_name="Patch web tier",
        nodes=_nodes(),
        block_lookup=_lookup(),
    )
    # technical: 2 automation steps
    assert [t.action for t in p.technical] == ["run_protection_job", "rolling_os_patching"]
    # narrative (non-technical/exec): composed from plain summaries, in order
    assert len(p.narrative) == 2
    assert "Take a backup snapshot" in p.narrative[0].text
    assert "Apply OS patches" in p.narrative[1].text
    # flowchart: Start, step, gate, step, Complete
    kinds = [f.kind for f in p.flowchart]
    assert kinds[0] == "start" and kinds[-1] == "end"
    assert "gate" in kinds
    # exec summary + rollback present
    assert p.summary.startswith("This change will:")
    assert "restore from snapshot" in p.rollback


def test_packet_is_deterministic():
    a = build_packet(workflow_id="w", workflow_name="W", nodes=_nodes(), block_lookup=_lookup())
    b = build_packet(workflow_id="w", workflow_name="W", nodes=_nodes(), block_lookup=_lookup())
    assert a.model_dump() == b.model_dump()


def test_prod_target_requires_approval():
    p = build_packet(workflow_id="w", workflow_name="W", nodes=_nodes(), block_lookup=_lookup())
    # targets web-prod-01 → prod → needs review
    assert p.requires_approval
    assert p.blast_radius == 1


def test_no_automation_steps_is_benign():
    nodes = [{"id": "s", "type": "start", "data": {}}, {"id": "e", "type": "end", "data": {}}]
    p = build_packet(workflow_id="w", workflow_name="W", nodes=nodes, block_lookup={})
    assert p.technical == []
    assert "no mutating" in p.summary


@pytest.fixture
def client():
    from app.platform import database
    from app.platform.app_factory import create_app
    from app.platform.config import get_settings
    from fastapi.testclient import TestClient

    database.reset_for_tests()
    get_settings.cache_clear()
    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.automation_catalog.application.seed import seed_templates
    from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

    seed_templates()
    seed_workflow_library()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def test_packet_endpoint(client):
    token = client.post(
        "/api/v1/auth/login", json={"username": "operator", "password": "operator123"}
    ).json()["access_token"]
    wf_id = client.get("/api/v1/canvas/workflows").json()[0]["id"]
    r = client.get(f"/api/v1/review/packet/{wf_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert "technical" in body and "narrative" in body and "flowchart" in body
    assert body["change_class"] in ("standard", "normal", "emergency")

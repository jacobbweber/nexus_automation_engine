"""Seed a large library of realistic, governed enterprise workflows across many teams.

So a fresh login is a *full* control plane — not an empty shell. Each workflow composes the
canvas node types like Lego: CMDB-driven dynamic inventory, change/approval gates, secret leasing,
cluster-aware lifecycle validation, telemetry, and backend automation across VMware / Pure /
Cohesity / ServiceNow / CyberArk / Terraform / Ansible. Workflows carry ownership metadata
(owner, team, tags) and varied review states (published, submitted-for-review, draft) so the
review inbox and the reporting view both have substance, plus seeded run telemetry.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.contexts.orchestration_canvas.domain.models import (
    Edge,
    Node,
    NodeType,
    ReviewState,
    RunStatus,
    Workflow,
    WorkflowGraph,
    WorkflowRun,
)
from app.contexts.orchestration_canvas.infrastructure.repository import CanvasRepository
from app.shared_kernel.ids import new_id

# A node spec in the seed DSL: (id, type, data). Edges: (source, target, source_handle|None).
NodeSpec = tuple[str, str, dict]
EdgeSpec = tuple[str, str, str | None]


def _graph(nodes: list[NodeSpec], edges: list[EdgeSpec]) -> WorkflowGraph:
    """Auto-lay-out a node/edge spec into a WorkflowGraph (left-to-right, lightly staggered)."""
    placed: list[Node] = []
    for i, (nid, ntype, data) in enumerate(nodes):
        placed.append(
            Node(
                id=nid,
                type=NodeType(ntype),
                position={"x": float(80 + i * 210), "y": float(120 + (i % 2) * 90)},
                data=data,
            )
        )
    built_edges = [
        Edge(id=new_id("edge"), source=s, target=t, sourceHandle=h) for (s, t, h) in edges
    ]
    return WorkflowGraph(nodes=placed, edges=built_edges)


# (name, team, owner, tags, review_state, description, nodes, edges, completed_runs, failed_runs)
WorkflowSpec = tuple[
    str, str, str, list[str], ReviewState, str, list[NodeSpec], list[EdgeSpec], int, int
]


def _library() -> list[WorkflowSpec]:
    PUB, SUB, DRAFT = ReviewState.PUBLISHED, ReviewState.SUBMITTED, ReviewState.DRAFT
    lib: list[WorkflowSpec] = []

    # ---- Storage team (Pure Storage) -------------------------------------------------------
    lib.append(
        (
            "Provision Datastore — Pure FlashArray",
            "Storage",
            "s.patel",
            ["pure", "datastore", "provisioning"],
            PUB,
            "Validate the change, lease array creds, create a volume and present it as a vVol "
            "datastore, then verify in the CMDB.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "ritm", "type": "string", "default": "RITM0012044"},
                            {"name": "size_tb", "type": "number", "default": 4},
                            {"name": "cluster", "type": "string", "default": "wld-prod-01"},
                        ],
                    },
                ),
                (
                    "chg",
                    "request_validation",
                    {
                        "name": "Validate RITM",
                        "reference": "{{start.ritm}}",
                        "required_state": "approved",
                    },
                ),
                (
                    "cred",
                    "secret_lease",
                    {
                        "name": "Lease array creds",
                        "safe": "storage-prod",
                        "object_name": "pure_api",
                        "bind_as": "array",
                    },
                ),
                (
                    "create",
                    "automation_task",
                    {
                        "name": "Create volume",
                        "connector": "purestorage",
                        "action": "create_volume",
                        "params": {"size_tb": "{{start.size_tb}}"},
                    },
                ),
                (
                    "present",
                    "automation_task",
                    {
                        "name": "Present as datastore",
                        "connector": "vmware",
                        "action": "create_datastore",
                        "params": {"cluster": "{{start.cluster}}"},
                    },
                ),
                (
                    "verify",
                    "cmdb_lookup",
                    {
                        "name": "Verify in CMDB",
                        "table": "cmdb_ci_storage_device",
                        "fields": ["name", "lifecycle_state", "cluster"],
                        "filters": {"env": "Production"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"datastore": "{{present.tail}}"}}),
            ],
            [
                ("start", "chg", None),
                ("chg", "cred", None),
                ("cred", "create", None),
                ("create", "present", None),
                ("present", "verify", None),
                ("verify", "end", None),
            ],
            37,
            2,
        )
    )
    lib.append(
        (
            "Decommission Datastore — guarded",
            "Storage",
            "s.patel",
            ["pure", "datastore", "destructive", "governed"],
            PUB,
            "Cluster-aware destructive workflow: confirm the CI, block if it "
            "is a cluster member, require human approval, then destroy and update the CMDB.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "datastore", "type": "string", "default": "ds-scratch"}
                        ],
                    },
                ),
                (
                    "ci",
                    "cmdb_lookup",
                    {
                        "name": "Lookup CI",
                        "table": "cmdb_ci_storage_device",
                        "fields": ["name", "cluster_member", "lifecycle_state"],
                        "filters": {"name": "{{start.datastore}}"},
                    },
                ),
                (
                    "guard",
                    "condition",
                    {
                        "name": "Cluster member?",
                        "variable": "{{ci.result.0.attributes.cluster_member}}",
                        "operator": "==",
                        "value": "True",
                        "case_sensitive": False,
                    },
                ),
                (
                    "blocked",
                    "variable_assigner",
                    {
                        "name": "Block",
                        "assignments": [
                            {"key": "outcome", "value": "rejected: cluster-member datastore"}
                        ],
                    },
                ),
                (
                    "approve",
                    "approval_gate",
                    {
                        "name": "Approve destroy",
                        "approver_roles": ["engineer", "admin"],
                        "message": "Approve destruction of {{start.datastore}}?",
                        "require_text_response": True,
                    },
                ),
                (
                    "destroy",
                    "automation_task",
                    {
                        "name": "Destroy volume",
                        "connector": "purestorage",
                        "action": "destroy_volume",
                        "params": {"target": "{{start.datastore}}"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {}}),
            ],
            [
                ("start", "ci", None),
                ("ci", "guard", None),
                ("guard", "blocked", "true"),
                ("guard", "approve", "false"),
                ("approve", "destroy", None),
                ("destroy", "end", None),
                ("blocked", "end", None),
            ],
            12,
            1,
        )
    )

    # ---- Compute team (VMware VCF) ---------------------------------------------------------
    lib.append(
        (
            "Patch ESXi Cluster — rolling",
            "Compute",
            "j.nguyen",
            ["vmware", "vcf", "patching", "maintenance"],
            PUB,
            "Pull cluster members from CMDB, enter maintenance mode host-by-host, remediate, and "
            "exit — inside an approved change window.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "cluster", "type": "string", "default": "wld-prod-01"},
                            {"name": "chg", "type": "string", "default": "CHG0044820"},
                        ],
                    },
                ),
                (
                    "chg",
                    "request_validation",
                    {
                        "name": "Validate CHG",
                        "reference": "{{start.chg}}",
                        "required_state": "approved",
                    },
                ),
                (
                    "hosts",
                    "cmdb_lookup",
                    {
                        "name": "Cluster hosts",
                        "table": "cmdb_ci_server",
                        "fields": ["name", "fqdn", "cluster"],
                        "filters": {"env": "Production"},
                    },
                ),
                (
                    "mm",
                    "automation_task",
                    {
                        "name": "Maintenance mode",
                        "connector": "vmware",
                        "action": "enter_maintenance_mode",
                        "params": {"hosts": "{{hosts.result}}"},
                    },
                ),
                (
                    "patch",
                    "automation_task",
                    {
                        "name": "Remediate baseline",
                        "connector": "vmware",
                        "action": "remediate_cluster",
                        "params": {"cluster": "{{start.cluster}}"},
                    },
                ),
                (
                    "exit",
                    "automation_task",
                    {
                        "name": "Exit maintenance",
                        "connector": "vmware",
                        "action": "exit_maintenance_mode",
                        "params": {"hosts": "{{hosts.result}}"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"patched": "{{patch.completed}}"}}),
            ],
            [
                ("start", "chg", None),
                ("chg", "hosts", None),
                ("hosts", "mm", None),
                ("mm", "patch", None),
                ("patch", "exit", None),
                ("exit", "end", None),
            ],
            21,
            3,
        )
    )
    lib.append(
        (
            "Provision VM from Template",
            "Compute",
            "j.nguyen",
            ["vmware", "vm", "provisioning", "self-service"],
            PUB,
            "Self-service VM build: validate request, clone from template, register the new CI in "
            "the CMDB, and hand back connection details.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "ritm", "type": "string", "default": "RITM0012050"},
                            {"name": "hostname", "type": "string", "default": "app-prod-09"},
                            {"name": "size", "type": "string", "default": "medium"},
                        ],
                    },
                ),
                (
                    "chg",
                    "request_validation",
                    {
                        "name": "Validate RITM",
                        "reference": "{{start.ritm}}",
                        "required_state": "approved",
                    },
                ),
                (
                    "size",
                    "switch_router",
                    {
                        "name": "Size profile",
                        "variable": "{{start.size}}",
                        "cases": [
                            {"value": "small", "handle": "case_small"},
                            {"value": "medium", "handle": "case_medium"},
                            {"value": "large", "handle": "case_large"},
                        ],
                        "default_handle": "case_medium",
                    },
                ),
                (
                    "clone",
                    "automation_task",
                    {
                        "name": "Clone VM",
                        "connector": "vmware",
                        "action": "clone_from_template",
                        "params": {"hostname": "{{start.hostname}}"},
                    },
                ),
                (
                    "register",
                    "automation_task",
                    {
                        "name": "Register CI",
                        "connector": "servicenow",
                        "action": "create_ci",
                        "params": {"name": "{{start.hostname}}"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"host": "{{start.hostname}}"}}),
            ],
            [
                ("start", "chg", None),
                ("chg", "size", None),
                ("size", "clone", "case_small"),
                ("size", "clone", "case_medium"),
                ("size", "clone", "case_large"),
                ("clone", "register", None),
                ("register", "end", None),
            ],
            58,
            4,
        )
    )

    # ---- Backup team (Cohesity) ------------------------------------------------------------
    lib.append(
        (
            "Onboard VM to Backup Policy",
            "Backup",
            "m.rossi",
            ["cohesity", "backup", "onboarding"],
            PUB,
            "Attach a newly built VM to the right Cohesity protection policy by environment, then "
            "trigger a first backup and confirm.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "vm", "type": "string", "default": "app-prod-09"},
                            {"name": "env", "type": "string", "default": "Production"},
                        ],
                    },
                ),
                (
                    "policy",
                    "switch_router",
                    {
                        "name": "Policy by env",
                        "variable": "{{start.env}}",
                        "cases": [
                            {"value": "Production", "handle": "case_gold"},
                            {"value": "Staging", "handle": "case_silver"},
                        ],
                        "default_handle": "case_bronze",
                    },
                ),
                (
                    "attach",
                    "automation_task",
                    {
                        "name": "Attach policy",
                        "connector": "cohesity",
                        "action": "protect_object",
                        "params": {"object": "{{start.vm}}"},
                    },
                ),
                (
                    "first",
                    "automation_task",
                    {
                        "name": "First backup",
                        "connector": "cohesity",
                        "action": "run_backup_now",
                        "params": {"object": "{{start.vm}}"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"protected": "{{attach.completed}}"}}),
            ],
            [
                ("start", "policy", None),
                ("policy", "attach", "case_gold"),
                ("policy", "attach", "case_silver"),
                ("policy", "attach", "case_bronze"),
                ("attach", "first", None),
                ("first", "end", None),
            ],
            44,
            1,
        )
    )
    lib.append(
        (
            "Restore VM from Snapshot",
            "Backup",
            "m.rossi",
            ["cohesity", "restore", "approval", "governed"],
            SUB,
            "Recovery workflow with approval: pick a recovery point, get sign-off, restore, "
            "and verify the VM is back.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "vm", "type": "string", "default": "db-prod-01"},
                            {"name": "point", "type": "string", "default": "latest"},
                        ],
                    },
                ),
                (
                    "approve",
                    "approval_gate",
                    {
                        "name": "Approve restore",
                        "approver_roles": ["engineer"],
                        "message": "Approve restore of {{start.vm}} to {{start.point}}?",
                    },
                ),
                (
                    "restore",
                    "automation_task",
                    {
                        "name": "Restore",
                        "connector": "cohesity",
                        "action": "recover_object",
                        "params": {"object": "{{start.vm}}"},
                    },
                ),
                (
                    "verify",
                    "telemetry_probe",
                    {"name": "Verify health", "entity": "{{start.vm}}", "seconds": 120},
                ),
                ("end", "end", {"name": "End", "outputs": {"restored": "{{restore.completed}}"}}),
            ],
            [
                ("start", "approve", None),
                ("approve", "restore", None),
                ("restore", "verify", None),
                ("verify", "end", None),
            ],
            6,
            0,
        )
    )

    # ---- ITSM team (ServiceNow) ------------------------------------------------------------
    lib.append(
        (
            "RITM Fulfillment — Standard Server Build",
            "ITSM",
            "a.khan",
            ["servicenow", "ritm", "fulfillment", "standard-change"],
            PUB,
            "End-to-end standard catalog fulfillment: validate the RITM, build via Terraform + "
            "Ansible, register the CI, and close the request.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [{"name": "ritm", "type": "string", "default": "RITM0012066"}],
                    },
                ),
                (
                    "chg",
                    "request_validation",
                    {
                        "name": "Validate RITM",
                        "reference": "{{start.ritm}}",
                        "required_state": "approved",
                    },
                ),
                (
                    "infra",
                    "automation_task",
                    {
                        "name": "Terraform apply",
                        "connector": "terraform",
                        "action": "apply",
                        "params": {"workspace": "standard-server"},
                    },
                ),
                (
                    "config",
                    "automation_task",
                    {
                        "name": "Ansible configure",
                        "connector": "ansible",
                        "action": "run_job_template",
                        "params": {"playbooks": ["baseline.yml"]},
                    },
                ),
                (
                    "ci",
                    "automation_task",
                    {
                        "name": "Register CI",
                        "connector": "servicenow",
                        "action": "create_ci",
                        "params": {},
                    },
                ),
                (
                    "close",
                    "automation_task",
                    {
                        "name": "Close RITM",
                        "connector": "servicenow",
                        "action": "close_request",
                        "params": {"reference": "{{start.ritm}}"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {}}),
            ],
            [
                ("start", "chg", None),
                ("chg", "infra", None),
                ("infra", "config", None),
                ("config", "ci", None),
                ("ci", "close", None),
                ("close", "end", None),
            ],
            73,
            5,
        )
    )
    lib.append(
        (
            "CMDB CI Validation Sweep",
            "ITSM",
            "a.khan",
            ["servicenow", "cmdb", "compliance", "reporting"],
            PUB,
            "Governance sweep: pull all production CIs, flag any that are retired or have stale "
            "lifecycle data for review.",
            [
                ("start", "start", {"name": "Start", "inputs": []}),
                (
                    "all",
                    "cmdb_lookup",
                    {
                        "name": "All prod CIs",
                        "table": "cmdb_ci",
                        "fields": ["name", "ci_type", "lifecycle_state", "cluster"],
                        "filters": {"env": "Production"},
                        "limit": 200,
                    },
                ),
                (
                    "any",
                    "condition",
                    {
                        "name": "Any retired?",
                        "variable": "{{all.count}}",
                        "operator": ">",
                        "value": "0",
                    },
                ),
                (
                    "report",
                    "template_transform",
                    {
                        "name": "Build report",
                        "template": "Reviewed {{count}} CIs.",
                        "variables": {"count": "{{all.count}}"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"report": "{{report.result}}"}}),
            ],
            [
                ("start", "all", None),
                ("all", "any", None),
                ("any", "report", "true"),
                ("any", "end", "false"),
                ("report", "end", None),
            ],
            90,
            0,
        )
    )

    # ---- Security / IAM team (CyberArk) ----------------------------------------------------
    lib.append(
        (
            "Rotate Service Account Credential",
            "Security",
            "d.olsen",
            ["cyberark", "iam", "rotation", "scheduled"],
            PUB,
            "Lease the current credential, rotate on the target, confirm — designed to run on "
            "a schedule.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [{"name": "account", "type": "string", "default": "svc_app"}],
                    },
                ),
                (
                    "lease",
                    "secret_lease",
                    {
                        "name": "Lease current",
                        "safe": "prod",
                        "object_name": "{{start.account}}",
                        "bind_as": "current",
                    },
                ),
                (
                    "rotate",
                    "automation_task",
                    {
                        "name": "Rotate",
                        "connector": "ansible",
                        "action": "run_job_template",
                        "params": {"playbooks": ["rotate_credential.yml"]},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"rotated": "{{rotate.completed}}"}}),
            ],
            [("start", "lease", None), ("lease", "rotate", None), ("rotate", "end", None)],
            120,
            2,
        )
    )
    lib.append(
        (
            "Emergency Access Grant — break-glass",
            "Security",
            "d.olsen",
            ["cyberark", "iam", "break-glass", "approval", "governed"],
            SUB,
            "Time-boxed privileged access with dual approval and auto-expiry before access is "
            "revoked.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "user", "type": "string", "default": "oncall.eng"},
                            {"name": "minutes", "type": "number", "default": 60},
                        ],
                    },
                ),
                (
                    "approve",
                    "approval_gate",
                    {
                        "name": "Dual approval",
                        "approver_roles": ["admin"],
                        "message": "Grant break-glass to {{start.user}} for {{start.minutes}}m?",
                        "require_text_response": True,
                    },
                ),
                (
                    "grant",
                    "automation_task",
                    {
                        "name": "Grant access",
                        "connector": "ansible",
                        "action": "run_job_template",
                        "params": {"playbooks": ["grant_access.yml"]},
                    },
                ),
                (
                    "wait",
                    "delay",
                    {
                        "name": "Access window",
                        "delay_seconds": 5,
                        "reason": "Time-boxed access window (compressed for simulation).",
                    },
                ),
                (
                    "revoke",
                    "automation_task",
                    {
                        "name": "Revoke access",
                        "connector": "ansible",
                        "action": "run_job_template",
                        "params": {"playbooks": ["revoke_access.yml"]},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {}}),
            ],
            [
                ("start", "approve", None),
                ("approve", "grant", None),
                ("grant", "wait", None),
                ("wait", "revoke", None),
                ("revoke", "end", None),
            ],
            3,
            0,
        )
    )

    # ---- Platform / SRE team ---------------------------------------------------------------
    lib.append(
        (
            "Terraform Plan → Apply with Approval",
            "Platform",
            "l.meyer",
            ["terraform", "iac", "approval", "governed"],
            PUB,
            "Plan infrastructure changes, pause for human review of the plan, then apply only on "
            "approval.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "workspace", "type": "string", "default": "shared-network"}
                        ],
                    },
                ),
                (
                    "plan",
                    "automation_task",
                    {
                        "name": "Plan",
                        "connector": "terraform",
                        "action": "plan",
                        "params": {"workspace": "{{start.workspace}}"},
                    },
                ),
                (
                    "approve",
                    "approval_gate",
                    {
                        "name": "Review plan",
                        "approver_roles": ["engineer"],
                        "message": "Apply the plan for {{start.workspace}}?",
                    },
                ),
                (
                    "apply",
                    "automation_task",
                    {
                        "name": "Apply",
                        "connector": "terraform",
                        "action": "apply",
                        "params": {"workspace": "{{start.workspace}}"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"applied": "{{apply.completed}}"}}),
            ],
            [
                ("start", "plan", None),
                ("plan", "approve", None),
                ("approve", "apply", None),
                ("apply", "end", None),
            ],
            64,
            6,
        )
    )
    lib.append(
        (
            "Incident Auto-Remediation — High CPU",
            "Platform",
            "l.meyer",
            ["dynatrace", "sre", "remediation", "self-healing"],
            PUB,
            "Probe Dynatrace for high CPU; if over threshold, scale out and re-check, else no-op.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [{"name": "host", "type": "string", "default": "web-prod-01"}],
                    },
                ),
                (
                    "probe",
                    "telemetry_probe",
                    {"name": "CPU probe", "entity": "{{start.host}}", "seconds": 60},
                ),
                (
                    "hot",
                    "condition",
                    {
                        "name": "CPU > 85%?",
                        "variable": "{{probe.peak_cpu}}",
                        "operator": ">=",
                        "value": "85",
                    },
                ),
                (
                    "scale",
                    "automation_task",
                    {
                        "name": "Scale out",
                        "connector": "ansible",
                        "action": "run_job_template",
                        "params": {"playbooks": ["scale_out.yml"]},
                    },
                ),
                (
                    "noop",
                    "variable_assigner",
                    {"name": "No action", "assignments": [{"key": "action", "value": "none"}]},
                ),
                ("end", "end", {"name": "End", "outputs": {}}),
            ],
            [
                ("start", "probe", None),
                ("probe", "hot", None),
                ("hot", "scale", "true"),
                ("hot", "noop", "false"),
                ("scale", "end", None),
                ("noop", "end", None),
            ],
            88,
            7,
        )
    )

    # ---- Networking team -------------------------------------------------------------------
    lib.append(
        (
            "Firewall Rule Request",
            "Networking",
            "p.alvarez",
            ["nsx", "firewall", "approval", "governed"],
            DRAFT,
            "Operator-submitted firewall change: validate the request, get security approval, push "
            "the rule, and confirm.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [
                            {"name": "ritm", "type": "string", "default": "RITM0012088"},
                            {"name": "src", "type": "string", "default": "10.20.0.0/24"},
                            {"name": "dst", "type": "string", "default": "10.30.5.10"},
                            {"name": "port", "type": "number", "default": 443},
                        ],
                    },
                ),
                (
                    "chg",
                    "request_validation",
                    {
                        "name": "Validate RITM",
                        "reference": "{{start.ritm}}",
                        "required_state": "approved",
                    },
                ),
                (
                    "approve",
                    "approval_gate",
                    {
                        "name": "Security approval",
                        "approver_roles": ["admin"],
                        "message": "Approve {{start.src}} → {{start.dst}}:{{start.port}}?",
                    },
                ),
                (
                    "push",
                    "automation_task",
                    {
                        "name": "Push rule",
                        "connector": "ansible",
                        "action": "run_job_template",
                        "params": {"playbooks": ["nsx_firewall.yml"]},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {}}),
            ],
            [
                ("start", "chg", None),
                ("chg", "approve", None),
                ("approve", "push", None),
                ("push", "end", None),
            ],
            0,
            0,
        )
    )

    # ---- DR (guaranteed by the DR-Tier-0 pinning rule, M27) ---------------------------------
    lib.append(
        (
            "Zerto DR VPG",
            "Platform",
            "a.khan",
            ["dr", "zerto", "replication", "governed"],
            PUB,
            "Ensure a Zerto Virtual Protection Group exists for a DR-Tier-0 VM: create/verify the "
            "VPG and confirm the protection state in the CMDB.",
            [
                (
                    "start",
                    "start",
                    {
                        "name": "Start",
                        "inputs": [{"name": "vm", "type": "string", "default": "db-prod-01"}],
                    },
                ),
                (
                    "vpg",
                    "automation_task",
                    {
                        "name": "Ensure Zerto VPG",
                        "connector": "script",
                        "action": "ensure_zerto_vpg",
                        "params": {"target": "{{start.vm}}"},
                    },
                ),
                (
                    "verify",
                    "cmdb_lookup",
                    {
                        "name": "Verify protection",
                        "table": "cmdb_ci_server",
                        "fields": ["name", "env"],
                        "filters": {"env": "Production"},
                    },
                ),
                ("end", "end", {"name": "End", "outputs": {"vpg": "{{vpg.tail}}"}}),
            ],
            [
                ("start", "vpg", None),
                ("vpg", "verify", None),
                ("verify", "end", None),
            ],
            5,
            0,
        )
    )

    return lib


def _seed_runs(repo: CanvasRepository, workflow_id: str, completed: int, failed: int) -> None:
    """Seed believable run telemetry spread over the last ~30 days."""
    now = datetime.now(UTC)
    total = completed + failed
    for i in range(total):
        is_fail = i >= completed
        started = now - timedelta(days=(total - i) % 30, hours=(i * 7) % 24)
        repo.save_run(
            WorkflowRun(
                run_id=new_id("run"),
                workflow_id=workflow_id,
                status=RunStatus.FAILED if is_fail else RunStatus.COMPLETED,
                started_at=started,
                completed_at=started + timedelta(minutes=2),
                inputs={},
                outputs={} if is_fail else {"ok": True},
                error_message="Simulated failure" if is_fail else None,
            )
        )


def seed_workflow_library(repo: CanvasRepository | None = None) -> int:
    """Seed the workflow library only when the canvas is empty (idempotent). Returns count."""
    repo = repo or CanvasRepository()
    if repo.count_workflows() > 0:
        return 0
    now = datetime.now(UTC)
    created = 0
    for name, team, owner, tags, state, desc, nodes, edges, ok, bad in _library():
        wf_id = new_id("wf")
        repo.save_workflow(
            Workflow(
                id=wf_id,
                name=name,
                description=desc,
                graph=_graph(nodes, edges),
                owner=owner,
                team=team,
                tags=tags,
                created_at=now,
                updated_at=now,
            )
        )
        if state != ReviewState.DRAFT:
            reviewer = (
                "reviewer" if state in (ReviewState.PUBLISHED, ReviewState.APPROVED) else None
            )
            repo.set_review_state(wf_id, state, submitted_by=owner, reviewed_by=reviewer)
        _seed_runs(repo, wf_id, ok, bad)
        created += 1
    return created

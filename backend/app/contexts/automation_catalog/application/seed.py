"""Seed a large, believable catalog so the faceted operator UX has real substance.

Covers VMware VCF 9, Pure Storage (FlashArray), Cohesity, ServiceNow (via Ansible), plus generic
Ansible/Terraform/script — with domain/vendor/tags/risk metadata. Connector + action pairs match
the simulation adapters so every catalog item actually runs.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.contexts.automation_catalog.domain.models import (
    ApprovalState,
    SurveyField,
    Template,
)
from app.contexts.automation_catalog.infrastructure.repository import TemplateRepository
from app.contexts.connectors.domain.models import ConnectorKind
from app.shared_kernel.idempotency import infer_idempotency
from app.shared_kernel.ids import new_id

A = ConnectorKind  # shorthand

# (name, connector, action, domain, vendor, tags, risk, atomic, minutes, description)
_CATALOG: list[tuple] = [
    # --- VMware VCF 9 (Compute) ---
    (
        "Deploy VCF Workload Domain",
        A.VMWARE,
        "deploy_workload_domain",
        "Compute",
        "VMware",
        ["vcf", "sddc", "provisioning"],
        "high",
        False,
        90,
        "Stand up a new VCF 9 workload domain: commission hosts, build cluster, deploy NSX, vSAN.",
    ),
    (
        "Add ESXi Host to Cluster",
        A.VMWARE,
        "add_esxi_host",
        "Compute",
        "VMware",
        ["vcf", "esxi", "scale-out"],
        "medium",
        True,
        20,
        "Commission and add an ESXi host to an existing workload-domain cluster.",
    ),
    (
        "vMotion Virtual Machine",
        A.VMWARE,
        "vmotion",
        "Compute",
        "VMware",
        ["vmotion", "migration"],
        "low",
        True,
        5,
        "Live-migrate a running VM to another host with zero downtime.",
    ),
    (
        "Create vVol Datastore",
        A.VMWARE,
        "create_datastore",
        "Storage",
        "VMware",
        ["datastore", "vvol", "storage"],
        "medium",
        True,
        10,
        "Register a VASA provider and create + mount a vVol datastore across the cluster.",
    ),
    (
        "Delete Datastore",
        A.VMWARE,
        "delete_datastore",
        "Storage",
        "VMware",
        ["datastore", "destructive"],
        "critical",
        True,
        10,
        "Unmount and delete a datastore. CONTROLLED — verifies no registered VMs first.",
    ),
    (
        "Deploy NSX Edge Cluster",
        A.VMWARE,
        "nsx_edge_deploy",
        "Network",
        "VMware",
        ["nsx", "edge", "bgp"],
        "high",
        False,
        45,
        "Deploy an NSX-T edge cluster with Tier-0 gateway and BGP peering.",
    ),
    # --- Pure Storage (Storage) ---
    (
        "Provision FlashArray Volume",
        A.PURESTORAGE,
        "create_volume",
        "Storage",
        "Pure Storage",
        ["pure", "volume", "provisioning"],
        "low",
        True,
        5,
        "Create a FlashArray volume with a QoS policy (Ansible purefa_volume).",
    ),
    (
        "Snapshot Volume",
        A.PURESTORAGE,
        "snapshot_volume",
        "Storage",
        "Pure Storage",
        ["pure", "snapshot", "data-protection"],
        "low",
        True,
        3,
        "Take a point-in-time snapshot of a FlashArray volume.",
    ),
    (
        "Eradicate Volume",
        A.PURESTORAGE,
        "eradicate_volume",
        "Storage",
        "Pure Storage",
        ["pure", "destructive"],
        "critical",
        True,
        5,
        "Destroy and eradicate a volume (unrecoverable). CONTROLLED.",
    ),
    (
        "Connect Volume to Host",
        A.PURESTORAGE,
        "connect_host",
        "Storage",
        "Pure Storage",
        ["pure", "host", "san"],
        "medium",
        True,
        5,
        "Create a host object and connect a volume (LUN mapping).",
    ),
    (
        "Create Protection Group + Replication",
        A.PURESTORAGE,
        "create_protection_group",
        "Storage",
        "Pure Storage",
        ["pure", "replication", "dr"],
        "medium",
        False,
        15,
        "Create a protection group and schedule async replication to the DR array.",
    ),
    # --- Cohesity (Backup) ---
    (
        "Run Protection Job",
        A.COHESITY,
        "run_backup",
        "Backup",
        "Cohesity",
        ["cohesity", "backup"],
        "low",
        True,
        30,
        "Trigger an on-demand Cohesity protection job (CBT incremental + dedup).",
    ),
    (
        "Recover VM",
        A.COHESITY,
        "recover_vm",
        "Backup",
        "Cohesity",
        ["cohesity", "recovery", "dr"],
        "high",
        False,
        20,
        "Instant-recover a VM from the latest (or chosen) recovery point.",
    ),
    (
        "Clone VM for Test/Dev",
        A.COHESITY,
        "clone_vm",
        "Backup",
        "Cohesity",
        ["cohesity", "clone", "testdev"],
        "low",
        True,
        10,
        "Create a zero-cost clone of a production VM into a test network.",
    ),
    (
        "Add Object to Protection Policy",
        A.COHESITY,
        "protect_object",
        "Backup",
        "Cohesity",
        ["cohesity", "policy"],
        "low",
        True,
        5,
        "Register and add an object to a Cohesity protection policy.",
    ),
    # --- ServiceNow via Ansible (ITSM) ---
    (
        "Sync CMDB Inventory Snapshot",
        A.ANSIBLE,
        "run_job_template",
        "ITSM",
        "ServiceNow",
        ["servicenow", "cmdb", "inventory"],
        "low",
        True,
        8,
        "Reconcile discovered infrastructure into the ServiceNow CMDB.",
    ),
    (
        "Fulfill RITM — VM Provision Request",
        A.ANSIBLE,
        "run_job_template",
        "ITSM",
        "ServiceNow",
        ["servicenow", "ritm", "fulfillment"],
        "medium",
        False,
        25,
        "End-to-end fulfillment of a catalog RITM: provision, configure, update the request.",
    ),
    (
        "Close Change on Success",
        A.ANSIBLE,
        "run_job_template",
        "ITSM",
        "ServiceNow",
        ["servicenow", "change"],
        "low",
        True,
        3,
        "Update and close a ServiceNow change record after a successful implementation.",
    ),
    (
        "Create Incident from Alert",
        A.ANSIBLE,
        "run_job_template",
        "ITSM",
        "ServiceNow",
        ["servicenow", "incident"],
        "low",
        True,
        2,
        "Open a ServiceNow incident from a monitoring alert with enrichment.",
    ),
    # --- Ansible config mgmt (Compute/Security) ---
    (
        "RHEL 9 CIS/STIG Hardening",
        A.ANSIBLE,
        "run_job_template",
        "Security",
        "Ansible",
        ["compliance", "cis", "stig", "rhel"],
        "high",
        True,
        25,
        "Apply CIS/STIG hardening to RHEL 9 hosts (check-mode preview supported).",
    ),
    (
        "Rolling OS Patching",
        A.ANSIBLE,
        "run_job_template",
        "Compute",
        "Ansible",
        ["patching", "maintenance"],
        "high",
        False,
        60,
        "Rolling security patches across a fleet with health checks between batches.",
    ),
    (
        "Rotate Service Account Credentials",
        A.ANSIBLE,
        "run_job_template",
        "Security",
        "Ansible",
        ["secrets", "rotation"],
        "medium",
        True,
        10,
        "Rotate service-account credentials and update dependent services.",
    ),
    # --- Terraform (Compute/Network) ---
    (
        "Provision AWS EKS Cluster",
        A.TERRAFORM,
        "apply",
        "Compute",
        "Terraform",
        ["terraform", "eks", "kubernetes"],
        "high",
        False,
        30,
        "Provision an EKS cluster and node groups (pair with an approval gate for prod).",
    ),
    (
        "Plan VPC + Subnet Topology",
        A.TERRAFORM,
        "plan",
        "Network",
        "Terraform",
        ["terraform", "vpc", "network"],
        "low",
        True,
        5,
        "Dry-run a VPC/subnet topology change and review the plan.",
    ),
    (
        "Destroy Sandbox Environment",
        A.TERRAFORM,
        "destroy",
        "Compute",
        "Terraform",
        ["terraform", "destructive", "sandbox"],
        "high",
        True,
        15,
        "Tear down a sandbox environment. CONTROLLED.",
    ),
    # --- Script / Day-2 ops ---
    (
        "Recycle IIS App Pool",
        A.SCRIPT,
        "run",
        "Compute",
        "Ansible",
        ["windows", "iis", "day2"],
        "low",
        True,
        2,
        "Recycle IIS application pools and clear caches on a Windows host (WinRM).",
    ),
    (
        "Clear Linux Disk Pressure",
        A.SCRIPT,
        "run",
        "Compute",
        "Ansible",
        ["linux", "disk", "day2"],
        "medium",
        True,
        5,
        "Reclaim disk on a Linux host: rotate logs, prune caches, report usage.",
    ),
]


def _survey_for(connector: ConnectorKind) -> list[SurveyField]:
    if connector == ConnectorKind.ANSIBLE:
        return [
            SurveyField(
                name="inventory",
                type="select",
                label="Target inventory",
                required=True,
                source="servicenow:cmdb_ci_server",
            )
        ]
    if connector == ConnectorKind.VMWARE:
        return [SurveyField(name="target", type="string", label="Target object", required=True)]
    if connector == ConnectorKind.PURESTORAGE:
        return [
            SurveyField(name="array", type="string", label="FlashArray", required=True),
            SurveyField(name="name", type="string", label="Object name", required=True),
        ]
    if connector == ConnectorKind.COHESITY:
        return [SurveyField(name="object", type="string", label="Object", required=True)]
    if connector == ConnectorKind.TERRAFORM:
        return [SurveyField(name="workspace", type="string", label="Workspace", required=True)]
    if connector == ConnectorKind.SCRIPT:
        return [SurveyField(name="target", type="string", label="Target host", required=True)]
    return []


def seed_templates(repo: TemplateRepository | None = None) -> int:
    repo = repo or TemplateRepository()
    if repo.count() > 0:
        return 0
    now = datetime.now(UTC)
    created = 0
    for name, connector, action, domain, vendor, tags, risk, atomic, minutes, desc in _CATALOG:
        repo.upsert(
            Template(
                id=new_id("tpl"),
                name=name,
                description=desc,
                connector=connector,
                action=action,
                markdown_documentation=f"# {name}\n\n{desc}\n\n**Vendor:** {vendor}  \n"
                f"**Domain:** {domain}  \n**Risk:** {risk}  \n**Est. duration:** ~{minutes} min\n",
                supports_check_mode=connector
                in (A.ANSIBLE, A.TERRAFORM, A.VMWARE, A.PURESTORAGE, A.COHESITY),
                supports_diff=connector in (A.ANSIBLE, A.TERRAFORM),
                idempotency=infer_idempotency(action),
                survey=_survey_for(connector),
                default_params={},
                owner="engineer",
                approval_state=ApprovalState.APPROVED,
                domain=domain,
                vendor=vendor,
                tags=tags,
                risk=risk,
                estimated_minutes=minutes,
                prerequisites=f"Access to {vendor} target; appropriate RBAC entitlement.",
                version="1.0.0",
                atomic=atomic,
                ci_type="datastore" if ("datastore" in tags or "datastore" in action) else "vm",
                ci_heritage=vendor,
                approved_date=now,
                last_reviewed=now,
                created_at=now,
                updated_at=now,
            )
        )
        created += 1
    return created

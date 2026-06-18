"""Seed a few approved building blocks so the catalog is populated on first run."""

from __future__ import annotations

from datetime import UTC, datetime

from app.contexts.automation_catalog.domain.models import (
    ApprovalState,
    SurveyField,
    Template,
)
from app.contexts.automation_catalog.infrastructure.repository import TemplateRepository
from app.contexts.connectors.domain.models import ConnectorKind
from app.shared_kernel.ids import new_id


def _tpl(**kwargs) -> Template:
    now = datetime.now(UTC)
    return Template(
        id=new_id("tpl"),
        owner="engineer",
        approval_state=ApprovalState.APPROVED,
        created_at=now,
        updated_at=now,
        **kwargs,
    )


def seed_templates(repo: TemplateRepository | None = None) -> int:
    repo = repo or TemplateRepository()
    if repo.count() > 0:
        return 0

    templates = [
        _tpl(
            name="Provision AWS EKS Cluster & Node Groups",
            description="Stand up an EKS cluster and its worker node groups via Terraform.",
            connector=ConnectorKind.TERRAFORM,
            action="apply",
            markdown_documentation="# EKS Provisioning\nApplies the EKS module. Pair with an "
            "approval gate for production.",
            supports_check_mode=True,
            supports_diff=True,
            survey=[
                SurveyField(
                    name="workspace",
                    type="select",
                    label="Workspace",
                    required=True,
                    choices=["dev", "staging", "prod-east"],
                ),
                SurveyField(
                    name="var_file", type="string", label="Var file", default="prod.tfvars"
                ),
            ],
            default_params={},
        ),
        _tpl(
            name="RHEL 9 CIS/STIG Compliance Enforcement",
            description="Apply CIS/STIG hardening playbooks to RHEL 9 hosts.",
            connector=ConnectorKind.ANSIBLE,
            action="run_job_template",
            markdown_documentation="# CIS/STIG Enforcement\nSupports check mode to preview "
            "changes before applying.",
            supports_check_mode=True,
            supports_diff=True,
            survey=[
                SurveyField(
                    name="inventory",
                    type="select",
                    label="Target inventory",
                    required=True,
                    source="servicenow:cmdb_ci_server",
                ),
                SurveyField(
                    name="playbooks", type="string", label="Playbooks", default="hardening.yml"
                ),
            ],
            default_params={"playbooks": ["hardening.yml"]},
        ),
        _tpl(
            name="Emergency IIS App Pool Recycle & Cache Clear",
            description="Recycle IIS application pools and clear caches on a Windows host.",
            connector=ConnectorKind.SCRIPT,
            action="run",
            markdown_documentation="# IIS Recycle\nFast WinRM jump-box operation.",
            survey=[
                SurveyField(name="target", type="string", label="Target host", required=True),
            ],
            default_params={
                "shell": "powershell",
                "transport": "winrm",
                "script": "Restart-WebAppPool DefaultAppPool",
            },
        ),
    ]
    for t in templates:
        repo.upsert(t)
    return len(templates)

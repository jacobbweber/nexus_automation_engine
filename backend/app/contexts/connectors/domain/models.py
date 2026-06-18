"""Vendor-neutral connector models.

These are the *only* vocabulary the rest of the system sees. A vendor's concepts (an AAP job
template, a Terraform run, a ServiceNow CI) are translated into these at the adapter boundary,
so vendor models never leak into the canvas, execution engine, or UI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ConnectorCategory(StrEnum):
    EXECUTION = "execution"  # runs work: ansible, terraform, script
    SYSTEM_OF_RECORD = "system_of_record"  # servicenow, cyberark, dynatrace


class ConnectorKind(StrEnum):
    ANSIBLE = "ansible"
    TERRAFORM = "terraform"
    SCRIPT = "script"
    SERVICENOW = "servicenow"
    CYBERARK = "cyberark"
    DYNATRACE = "dynatrace"


class ParamField(BaseModel):
    """One field in a connector action's parameter form (drives the canvas node UI)."""

    name: str
    type: str  # "string" | "number" | "boolean" | "select" | "list" | "code" | "keyvalue"
    label: str
    required: bool = False
    default: object | None = None
    choices: list[str] | None = None
    help: str | None = None


class ConnectorAction(BaseModel):
    name: str
    label: str
    description: str = ""
    params: list[ParamField] = Field(default_factory=list)


class Capabilities(BaseModel):
    """What a connector can do — surfaced to the canvas so nodes self-describe their forms."""

    kind: ConnectorKind
    category: ConnectorCategory
    display_name: str
    description: str = ""
    supports_check_mode: bool = False
    supports_diff: bool = False
    streams_logs: bool = True
    actions: list[ConnectorAction] = Field(default_factory=list)


# --- Execution -------------------------------------------------------------------------------


class RunState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StreamType(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    SYSTEM = "system"


class ExecutionRequest(BaseModel):
    kind: ConnectorKind
    action: str
    params: dict[str, object] = Field(default_factory=dict)
    check_mode: bool = False
    diff_mode: bool = False
    run_id: str | None = None


class LogEvent(BaseModel):
    timestamp: datetime = Field(default_factory=_utcnow)
    stream: StreamType = StreamType.STDOUT
    message: str  # may contain ANSI escape codes; the UI terminal renders them


class RunStatus(BaseModel):
    state: RunState
    exit_code: int | None = None
    message: str = ""


# --- Discovery (e.g. ServiceNow CMDB) --------------------------------------------------------


class DiscoveryQuery(BaseModel):
    source: str  # e.g. a CMDB table name
    filters: dict[str, object] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    limit: int = 50


class Resource(BaseModel):
    id: str
    name: str
    attributes: dict[str, object] = Field(default_factory=dict)


# --- Secret leasing (e.g. CyberArk) ----------------------------------------------------------


class SecretRequest(BaseModel):
    safe: str
    object_name: str


class CredentialLease(BaseModel):
    """A short-lived credential. NEVER persisted; lives only in memory for a run."""

    lease_id: str
    username: str
    secret: str
    expires_at: datetime


# --- Change/approval validation (e.g. ServiceNow request/change) -----------------------------


class ChangeValidation(BaseModel):
    ok: bool
    reference: str
    state: str
    reason: str = ""


# --- Telemetry (e.g. Dynatrace) --------------------------------------------------------------


class TelemetrySample(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float


class TelemetryEvent(BaseModel):
    timestamp: datetime
    severity: str  # "info" | "warning" | "error"
    title: str


class TelemetrySeries(BaseModel):
    samples: list[TelemetrySample] = Field(default_factory=list)
    events: list[TelemetryEvent] = Field(default_factory=list)

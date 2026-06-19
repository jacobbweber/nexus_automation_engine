"""Node-type parameter schemas — the single source of truth that drives the canvas property UI.

Each node type publishes a typed field list so the frontend renders proper, guided controls
(selects, toggles, numbers, key-value, multi-select, dynamic pickers) instead of raw JSON. Adding
a parameter is a one-line change here; the UI adapts automatically (extensibility on an individual
layer). ``source`` marks a field whose options are fetched dynamically (e.g. CMDB fields).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

CONDITION_OPERATORS = [
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "contains",
    "not_contains",
    "starts_with",
    "ends_with",
    "matches_regex",
    "in_list",
    "is_empty",
    "is_not_empty",
]


class NodeFieldSpec(BaseModel):
    name: str
    # string|number|boolean|select|multiselect|keyvalue|code|textarea|cases|assignments|inputs
    type: str
    label: str
    required: bool = False
    default: object | None = None
    choices: list[str] | None = None
    help: str = ""
    # dynamic options: cmdb_fields|cmdb_tables|execution_connectors|connector_actions|workflows
    source: str | None = None
    placeholder: str = ""


class NodeTypeSpec(BaseModel):
    type: str
    label: str
    category: str
    description: str
    fields: list[NodeFieldSpec] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=lambda: ["output"])  # handle ids


def _f(name: str, type: str, label: str, **kw) -> NodeFieldSpec:
    return NodeFieldSpec(name=name, type=type, label=label, **kw)


_RESILIENCE = [
    _f("max_retries", "number", "Max retries", default=0, help="Retry the node on failure."),
    _f("retry_delay_seconds", "number", "Retry delay (s)", default=1),
    _f("timeout_seconds", "number", "Timeout (s)", default=120),
]

NODE_SPECS: list[NodeTypeSpec] = [
    NodeTypeSpec(
        type="start",
        label="Start",
        category="Flow",
        description="Workflow entry point. Declares the inputs the run accepts.",
        fields=[_f("inputs", "inputs", "Run inputs", help="Name/type/default the run accepts.")],
    ),
    NodeTypeSpec(
        type="end",
        label="End",
        category="Flow",
        description="Terminates the run and compiles output values.",
        fields=[_f("outputs", "keyvalue", "Outputs", help="key → {{node.field}} expression.")],
        outputs=[],
    ),
    NodeTypeSpec(
        type="condition",
        label="Condition",
        category="Flow",
        description="Branch true/false on a rich comparison.",
        fields=[
            _f("variable", "string", "Left value", required=True, placeholder="{{node.field}}"),
            _f("operator", "select", "Operator", default="==", choices=CONDITION_OPERATORS),
            _f("value", "string", "Right value", placeholder="comparison value / regex / a,b,c"),
            _f("case_sensitive", "boolean", "Case sensitive", default=True),
        ],
        outputs=["true", "false"],
    ),
    NodeTypeSpec(
        type="switch_router",
        label="Switch",
        category="Flow",
        description="Route to a matching case by value.",
        fields=[
            _f("variable", "string", "Match value", required=True, placeholder="{{node.field}}"),
            _f("cases", "cases", "Cases", help="value → output handle."),
            _f("default_handle", "string", "Default handle", default="case_default"),
        ],
        outputs=["case_default"],
    ),
    NodeTypeSpec(
        type="delay",
        label="Delay",
        category="Flow",
        description="Pause the workflow for a fixed time.",
        fields=[
            _f("delay_seconds", "number", "Delay (seconds)", default=5, required=True),
            _f("reason", "string", "Reason", help="Why this pause exists (documentation)."),
        ],
    ),
    NodeTypeSpec(
        type="variable_assigner",
        label="Set Variable",
        category="Flow",
        description="Write/accumulate values into the run's variable pool.",
        fields=[_f("assignments", "assignments", "Assignments", help="key = {{expression}}.")],
    ),
    NodeTypeSpec(
        type="template_transform",
        label="Template",
        category="Flow",
        description="Render a Jinja2 template from pool values.",
        fields=[
            _f("template", "textarea", "Template", required=True),
            _f("variables", "keyvalue", "Variables"),
        ],
    ),
    NodeTypeSpec(
        type="http_request",
        label="HTTP Request",
        category="Integration",
        description="Call an external REST API (SSRF-guarded).",
        fields=[
            _f(
                "method",
                "select",
                "Method",
                default="GET",
                choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
            ),
            _f("url", "string", "URL", required=True),
            _f("headers", "keyvalue", "Headers"),
            _f("body", "textarea", "Body"),
            *_RESILIENCE,
        ],
    ),
    NodeTypeSpec(
        type="automation_task",
        label="Automation Task",
        category="Backend",
        description="Run a backend action (Ansible / Terraform / VMware / Pure / Cohesity).",
        fields=[
            _f("connector", "select", "Connector", required=True, source="execution_connectors"),
            _f("action", "select", "Action", required=True, source="connector_actions"),
            _f("params", "keyvalue", "Parameters"),
            _f("check_mode", "boolean", "Check mode (dry run)", default=False),
            _f("diff_mode", "boolean", "Diff mode", default=False),
            *_RESILIENCE,
        ],
    ),
    NodeTypeSpec(
        type="cmdb_lookup",
        label="CMDB Lookup",
        category="Backend",
        description="Query the ServiceNow CMDB for dynamic inventory.",
        fields=[
            _f("table", "select", "Table", default="cmdb_ci_server", source="cmdb_tables"),
            _f(
                "fields",
                "multiselect",
                "Return fields",
                source="cmdb_fields",
                help="Pick the CI fields to return.",
            ),
            _f("filters", "keyvalue", "Filters", help="field = value (e.g. env = Production)."),
            _f("limit", "number", "Limit", default=50),
        ],
    ),
    NodeTypeSpec(
        type="request_validation",
        label="Change Validation",
        category="Backend",
        description="Gate on an approved ServiceNow request/change.",
        fields=[
            _f("reference", "string", "RITM / CHG", required=True, placeholder="{{start.ritm}}"),
            _f(
                "required_state",
                "select",
                "Required state",
                default="approved",
                choices=["approved", "implement", "scheduled"],
            ),
        ],
    ),
    NodeTypeSpec(
        type="secret_lease",
        label="Secret Lease",
        category="Backend",
        description="Lease a short-lived credential from CyberArk (memory-only).",
        fields=[
            _f("safe", "string", "Safe", required=True),
            _f("object_name", "string", "Object", required=True),
            _f(
                "bind_as",
                "string",
                "Bind as",
                default="credential",
                help="Pool key downstream nodes reference.",
            ),
        ],
    ),
    NodeTypeSpec(
        type="telemetry_probe",
        label="Telemetry",
        category="Backend",
        description="Pull correlated Dynatrace metrics for a window.",
        fields=[
            _f("entity", "string", "Entity", required=True),
            _f("seconds", "number", "Window (s)", default=60),
        ],
    ),
    NodeTypeSpec(
        type="approval_gate",
        label="Approval Gate",
        category="Governance",
        description="Pause for human approval before continuing.",
        fields=[
            _f("message", "textarea", "Prompt", required=True),
            _f(
                "approver_roles",
                "multiselect",
                "Approver roles",
                source="roles",
                default=["engineer"],
            ),
            _f("require_text_response", "boolean", "Require a comment", default=False),
            _f("timeout_seconds", "number", "Timeout (s)", default=300),
        ],
    ),
    NodeTypeSpec(
        type="sub_workflow",
        label="Sub-Workflow",
        category="Composition",
        description="Run another saved workflow inline.",
        fields=[
            _f("workflow_id", "select", "Workflow", required=True, source="workflows"),
            _f("inputs", "keyvalue", "Inputs"),
        ],
    ),
]


def node_specs() -> list[NodeTypeSpec]:
    return NODE_SPECS

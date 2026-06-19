// Node palette catalogue for the canvas, grouped by category. Mirrors the backend NodeType enum.

export interface NodeTypeDef {
  type: string;
  label: string;
  desc: string;
}

export interface NodeCategory {
  name: string;
  color: string;
  types: NodeTypeDef[];
}

export const NODE_CATEGORIES: NodeCategory[] = [
  {
    name: "Flow",
    color: "var(--color-accent)",
    types: [
      { type: "start", label: "Start", desc: "Workflow entry + inputs" },
      { type: "end", label: "End", desc: "Compile outputs" },
      { type: "condition", label: "Condition", desc: "True/false branch" },
      { type: "switch_router", label: "Switch", desc: "Route by value" },
      { type: "delay", label: "Delay", desc: "Pause N seconds" },
      { type: "variable_assigner", label: "Set Variable", desc: "Write to the pool" },
      { type: "template_transform", label: "Template", desc: "Render Jinja text" },
    ],
  },
  {
    name: "Backend Integrations",
    color: "#d8a657",
    types: [
      { type: "automation_task", label: "Automation Task", desc: "Run Ansible/Terraform/script" },
      { type: "cmdb_lookup", label: "CMDB Lookup", desc: "ServiceNow inventory" },
      { type: "request_validation", label: "Change Validation", desc: "Gate on approved RITM/CHG" },
      { type: "secret_lease", label: "Secret Lease", desc: "CyberArk credential" },
      { type: "telemetry_probe", label: "Telemetry", desc: "Dynatrace metrics" },
      { type: "approval_gate", label: "Approval Gate", desc: "Human-in-the-loop" },
    ],
  },
  {
    name: "Composition",
    color: "#94ad92",
    types: [
      { type: "http_request", label: "HTTP Request", desc: "REST call" },
      { type: "sub_workflow", label: "Sub-Workflow", desc: "Run another workflow" },
    ],
  },
];

export function defaultData(type: string): Record<string, unknown> {
  switch (type) {
    case "automation_task":
      return { name: "Automation Task", connector: "ansible", action: "run_job_template", params: {} };
    case "condition":
      return { name: "Condition", variable: "{{start.value}}", operator: ">", value: "0" };
    case "cmdb_lookup":
      return { name: "CMDB Lookup", table: "cmdb_ci_server", filters: { env: "Production" } };
    case "request_validation":
      return { name: "Change Validation", reference: "{{start.ritm}}", required_state: "approved" };
    case "secret_lease":
      return { name: "Secret Lease", safe: "prod", object_name: "svc_account", bind_as: "credential" };
    case "telemetry_probe":
      return { name: "Telemetry", entity: "{{start.host}}", seconds: 60 };
    case "approval_gate":
      return { name: "Approval Gate", message: "Approve to proceed", approver_roles: ["engineer"] };
    case "delay":
      return { name: "Delay", delay_seconds: 3 };
    case "end":
      return { name: "End", outputs: {} };
    case "start":
      return { name: "Start", inputs: [] };
    default:
      return { name: type };
  }
}

export const ACCENT_BY_TYPE: Record<string, string> = Object.fromEntries(
  NODE_CATEGORIES.flatMap((c) => c.types.map((t) => [t.type, c.color])),
);

// Typed API client. Relative paths so the Vite dev proxy and container networking both work.

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

let authToken: string | null = localStorage.getItem("nexus_token");

export function setToken(token: string | null): void {
  authToken = token;
  if (token) localStorage.setItem("nexus_token", token);
  else localStorage.removeItem("nexus_token");
}

export function getToken(): string | null {
  return authToken;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  const res = await fetch(`/api/v1${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, payload.detail ?? payload.error ?? res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(p: string) => request<T>("GET", p),
  post: <T>(p: string, body?: unknown) => request<T>("POST", p, body),
  put: <T>(p: string, body?: unknown) => request<T>("PUT", p, body),
  del: <T>(p: string) => request<T>("DELETE", p),
};

// Opens an authenticated WebSocket to a backend path (token via query param, since browsers
// can't set headers on WebSocket connections).
export function openSocket(path: string): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const sep = path.includes("?") ? "&" : "?";
  const auth = authToken ? `${sep}token=${encodeURIComponent(authToken)}` : "";
  return new WebSocket(`${proto}://${window.location.host}/api/v1${path}${auth}`);
}

// --- typed resources ------------------------------------------------------------------------

export interface Health {
  status: string;
  app: string;
  version: string;
  environment: string;
  simulation_mode: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  global_role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ConnectorAction {
  name: string;
  label: string;
  description: string;
  params: ParamField[];
}
export interface ParamField {
  name: string;
  type: string;
  label: string;
  required: boolean;
  default: unknown;
  choices: string[] | null;
  help: string | null;
}
export interface Capabilities {
  kind: string;
  category: string;
  display_name: string;
  description: string;
  supports_check_mode: boolean;
  supports_diff: boolean;
  streams_logs: boolean;
  actions: ConnectorAction[];
}

export interface PlainSummary {
  input: string;
  action: string;
  outcome: string;
  rollback: string;
}
export interface Template {
  id: string;
  name: string;
  description: string;
  connector: string;
  action: string;
  markdown_documentation: string;
  supports_check_mode: boolean;
  supports_diff: boolean;
  idempotency: string; // idempotent | check_only | non_idempotent
  plain_summary: PlainSummary | null;
  survey: SurveyField[];
  default_params: Record<string, unknown>;
  owner: string;
  approval_state: string;
  domain: string;
  vendor: string;
  tags: string[];
  risk: string;
  estimated_minutes: number;
  prerequisites: string;
  version: string;
  atomic: boolean;
}

export interface CatalogFacets {
  domain: Record<string, number>;
  vendor: Record<string, number>;
}
export interface SurveyField {
  name: string;
  type: string;
  label: string;
  required: boolean;
  default: unknown;
  choices: string[] | null;
  source: string | null;
}

export interface Job {
  id: string;
  name: string;
  connector: string;
  action: string;
  status: string;
  initiated_by: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  graph: WorkflowGraph;
  review_state: string;
  submitted_by: string | null;
  reviewed_by: string | null;
  owner: string;
  team: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowUsage {
  workflow_id: string;
  run_count: number;
  success_count: number;
  failure_count: number;
  last_run_at: string | null;
  success_rate: number;
}
export interface WorkflowReport {
  id: string;
  name: string;
  description: string;
  owner: string;
  team: string;
  tags: string[];
  review_state: string;
  node_count: number;
  created_at: string;
  updated_at: string;
  usage: WorkflowUsage;
}
export interface WorkflowGraph {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  viewport: Record<string, number>;
}
export interface CanvasNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}
export interface CanvasEdge {
  id?: string | null;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
}

export interface RbacMatrix {
  roles: string[];
  capabilities: string[];
  matrix: Record<string, Record<string, boolean>>;
}

export const Auth = {
  login: (username: string, password: string) =>
    api.post<LoginResponse>("/auth/login", { username, password }),
  me: () => api.get<User>("/auth/me"),
  rbacMatrix: () => api.get<RbacMatrix>("/auth/rbac-matrix"),
  users: () => api.get<User[]>("/auth/users"),
};

export const Catalog = {
  list: (opts: { domain?: string; vendor?: string; search?: string } = {}) => {
    const q = new URLSearchParams();
    if (opts.domain) q.set("domain", opts.domain);
    if (opts.vendor) q.set("vendor", opts.vendor);
    if (opts.search) q.set("search", opts.search);
    const qs = q.toString();
    return api.get<Template[]>(`/catalog/templates${qs ? `?${qs}` : ""}`);
  },
  facets: () => api.get<CatalogFacets>("/catalog/facets"),
  get: (id: string) => api.get<Template>(`/catalog/templates/${id}`),
  execute: (id: string, survey_answers: Record<string, unknown>, check_mode = false) =>
    api.post<{ job_id: string; status: string }>(`/catalog/templates/${id}/execute`, {
      survey_answers,
      check_mode,
    }),
};

export const Jobs = {
  list: () => api.get<Job[]>("/jobs"),
  get: (id: string) => api.get<Job>(`/jobs/${id}`),
};

export interface CmdbField {
  name: string;
  label: string;
  type: string;
}
export interface CmdbFieldsResponse {
  tables: string[];
  fields: CmdbField[];
}

export interface ServiceNowChange {
  number: string;
  short_description: string;
  state: string;
  start: string;
  end: string;
  assignment_group: string;
  risk: string;
  affected_cis: string[];
}

export const Connectors = {
  list: () => api.get<Capabilities[]>("/connectors"),
  cmdbFields: (table?: string) =>
    api.get<CmdbFieldsResponse>(
      `/connectors/servicenow/fields${table ? `?table=${encodeURIComponent(table)}` : ""}`,
    ),
  changes: () => api.get<ServiceNowChange[]>("/connectors/servicenow/changes"),
  impact: (targets: string[]) =>
    api.post<ImpactItem[]>("/connectors/servicenow/impact", { targets }),
};

export interface ImpactItem {
  name: string;
  ci_type: string | null;
  cluster: string | null;
  reason: string;
}

export interface NodeFieldSpec {
  name: string;
  type: string;
  label: string;
  required: boolean;
  default: unknown;
  choices: string[] | null;
  help: string;
  source: string | null;
  placeholder: string;
}
export interface NodeTypeSpec {
  type: string;
  label: string;
  category: string;
  description: string;
  fields: NodeFieldSpec[];
  outputs: string[];
}

export interface WorkflowStep {
  step_id: string;
  run_id: string;
  node_id: string;
  node_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  retry_count: number;
  error_message: string | null;
}
export interface WorkflowRun {
  run_id: string;
  workflow_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  steps?: WorkflowStep[];
}

export const Canvas = {
  nodeTypes: () => api.get<NodeTypeSpec[]>("/canvas/node-types"),
  list: () => api.get<Workflow[]>("/canvas/workflows"),
  report: () => api.get<WorkflowReport[]>("/canvas/workflows/report"),
  runs: (id: string) => api.get<WorkflowRun[]>(`/canvas/workflows/${id}/runs`),
  getRun: (runId: string) => api.get<WorkflowRun>(`/canvas/runs/${runId}`),
  retryRun: (runId: string) => api.post<{ run_id: string }>(`/canvas/runs/${runId}/retry`),
  get: (id: string) => api.get<Workflow>(`/canvas/workflows/${id}`),
  save: (wf: {
    id?: string;
    name: string;
    description?: string;
    graph: WorkflowGraph;
    owner?: string;
    team?: string;
    tags?: string[];
  }) => api.post<Workflow>("/canvas/workflows", wf),
  remove: (id: string) => api.del<void>(`/canvas/workflows/${id}`),
  run: (id: string, inputs: Record<string, unknown>, plan = false) =>
    api.post<{ run_id: string }>(`/canvas/workflows/${id}/run`, { inputs, plan }),
  resolveApproval: (run_id: string, node_id: string, approved: boolean, response = "") =>
    api.post<{ resolved: boolean }>("/canvas/approvals/resolve", {
      run_id,
      node_id,
      approved,
      response,
    }),
  submitForReview: (id: string) => api.post<Workflow>(`/canvas/workflows/${id}/submit`),
  review: (id: string, decision: string, comment = "") =>
    api.post<Workflow>(`/canvas/workflows/${id}/review`, { decision, comment }),
  pendingReviews: () => api.get<Workflow[]>("/canvas/reviews/pending"),
};

export interface ChangeTemplate {
  id: string;
  name: string;
  short_description: string;
  assignment_group: string;
  category: string;
  risk: string;
  impact: string;
  cab_required: boolean;
}
export interface ChangeRecord {
  number: string;
  template_id: string | null;
  state: string;
  short_description: string;
  risk: string;
  assignment_group: string;
  cab_required: boolean;
  initiated_by: string;
  resource_type: string;
  resource_id: string;
  created_at: string;
  closed_at: string | null;
  close_code: string | null;
}

export const ChangeApi = {
  templates: () => api.get<ChangeTemplate[]>("/change/templates"),
  createTemplate: (t: Partial<ChangeTemplate> & { name: string }) =>
    api.post<ChangeTemplate>("/change/templates", t),
  records: () => api.get<ChangeRecord[]>("/change/records"),
  setPolicy: (p: {
    resource_type: string;
    resource_id: string;
    auto_change_control?: boolean;
    change_template_id?: string | null;
    require_approved_change?: boolean;
  }) => api.put<unknown>("/change/policies", p),
};

export interface Schedule {
  id: string;
  name: string;
  workflow_id: string;
  kind: string;
  interval_seconds: number;
  daily_time: string;
  enabled: boolean;
  next_run_at: string;
  last_run_at: string | null;
}

export const Schedules = {
  list: () => api.get<Schedule[]>("/schedules"),
  create: (s: { name: string; workflow_id: string; kind?: string; interval_seconds?: number }) =>
    api.post<Schedule>("/schedules", s),
  remove: (id: string) => api.del<void>(`/schedules/${id}`),
  runNow: (id: string) => api.post<{ run_id: string }>(`/schedules/${id}/run-now`),
};

export interface Incident {
  id: string;
  title: string;
  status: string;
  severity: string;
  source_type: string;
  source_id: string;
  summary: string;
  assigned_to: string | null;
  remediation_workflow_id: string | null;
  opened_at: string;
  resolved_at: string | null;
}

export const Incidents = {
  board: () => api.get<Record<string, Incident[]>>("/incidents/board"),
  move: (id: string, status: string) =>
    api.post<Incident>(`/incidents/${id}/move`, { status }),
  remediate: (id: string) => api.post<{ workflow_id: string }>(`/incidents/${id}/remediate`),
};

export interface ValidationPolicy {
  id: string;
  required_fields: string[];
  max_review_age_days: number;
  enforce_cmdb_consistency: boolean;
  reject_retired: boolean;
  reject_unknown_ci: boolean;
  block_destructive_on_cluster: boolean;
  updated_by: string;
  updated_at: string;
}

export interface ReviewStatus {
  fresh: number;
  stale: number;
  never_reviewed: number;
  total: number;
  oldest: { id: string; name: string; last_reviewed: string; vendor: string }[];
}

export const Validation = {
  policy: () => api.get<ValidationPolicy>("/governance/validation/policy"),
  updatePolicy: (p: ValidationPolicy) => api.put<ValidationPolicy>("/governance/validation/policy", p),
  reviewStatus: () => api.get<ReviewStatus>("/governance/validation/review-status"),
};

// --- CMDB schema, lineage & health (v4.0 Pillar A) ----
export interface CmdbFieldDef {
  name: string;
  label: string;
  datatype: string; // string | integer | boolean | enum | datetime | reference
  required: boolean;
  allowed_values: string[] | null;
  regex: string | null;
  default: string | null;
  sensitive: boolean;
}
export interface CITypeSchema {
  type: string;
  label: string;
  version: number;
  description: string;
  fields: CmdbFieldDef[];
  required_tags: string[];
  naming_pattern: string | null;
  updated_by: string;
  updated_at: string;
}
export interface LineageRelationship {
  name: string;
  target_type: string;
  direction: string; // up | down
  cardinality: string; // one | many
  required: boolean;
}
export interface LineageSpec {
  type: string;
  relationships: LineageRelationship[];
}
export interface CIHealthIssue {
  code: string;
  target: string;
  message: string;
  severity: string; // error | warning
  weight: number;
}
export interface CIHealthReport {
  ci_id: string;
  ci_type: string;
  status: string; // healthy | degraded | unhealthy
  score: number;
  field_issues: CIHealthIssue[];
  lineage_issues: CIHealthIssue[];
  tag_issues: CIHealthIssue[];
  remediation_hints: string[];
}

// --- GitOps config-as-code (v4.0 Pillar E) ----
export interface GitCommit {
  sha: string;
  message: string;
  date: string;
  author: string;
}
export interface RepoStatus {
  available: boolean;
  path: string;
  head: string | null;
  dirty: boolean;
  commits: number;
}
export interface PullDiffItem {
  path: string;
  change: string;
}
export interface PullPreview {
  differences: PullDiffItem[];
  in_sync: boolean;
}

export const GitOps = {
  status: () => api.get<RepoStatus>("/gitops/status"),
  sync: () => api.post<RepoStatus>("/gitops/sync"),
  history: (path?: string) =>
    api.get<GitCommit[]>(`/gitops/history${path ? `?path=${encodeURIComponent(path)}` : ""}`),
  diff: (path: string, a: string, b = "HEAD") =>
    api.get<{ diff: string }>(`/gitops/diff?path=${encodeURIComponent(path)}&a=${a}&b=${b}`),
  pullPreview: () => api.get<PullPreview>("/gitops/pull-preview"),
};

// --- deterministic pinning / guardrails (v4.0 Pillar D) ----
export interface PinningSelector {
  ci_type: string | null;
  tag_predicates: Record<string, string>;
  field_predicates: Record<string, string>;
}
export interface PinningRule {
  id: string;
  name: string;
  enabled: boolean;
  priority: number;
  selector: PinningSelector;
  workflow: string;
  trigger: string; // on_create | on_change | on_schedule | on_demand
  enforcement: string; // assert | enforce | gate
  description: string;
}
export interface RuleCoverage {
  rule_id: string;
  rule_name: string;
  enforcement: string;
  workflow: string;
  workflow_exists: boolean;
  matched: number;
  compliant: number;
  drifted: number;
  unknown: number;
}
export interface Coverage {
  total_cis: number;
  rules: RuleCoverage[];
}
export interface PinnedAction {
  ci: string;
  ci_type: string;
  rule_id: string;
  rule_name: string;
  workflow: string;
  enforcement: string;
  trigger: string;
  note: string;
}

export const Determinism = {
  rules: () => api.get<PinningRule[]>("/determinism/rules"),
  saveRule: (rule: PinningRule) => api.put<PinningRule>(`/determinism/rules/${rule.id}`, rule),
  deleteRule: (id: string) => api.del<{ deleted: boolean }>(`/determinism/rules/${id}`),
  coverage: () => api.get<Coverage>("/determinism/coverage"),
  reconcile: () => api.post<PinnedAction[]>("/determinism/reconcile"),
};

// --- multi-audience review & approval (v4.0 Pillar C) ----
export interface TechnicalStep {
  node_id: string;
  name: string;
  connector: string;
  action: string;
  params: Record<string, unknown>;
  idempotency: string;
}
export interface NarrativeStep {
  step: number;
  text: string;
}
export interface ReviewFlowPhase {
  label: string;
  kind: string;
}
export interface ReviewPacket {
  workflow_id: string;
  workflow_name: string;
  change_class: string;
  required_level: string;
  requires_approval: boolean;
  reasons: string[];
  risk: string;
  blast_radius: number;
  technical: TechnicalStep[];
  narrative: NarrativeStep[];
  flowchart: ReviewFlowPhase[];
  summary: string;
  rollback: string;
}
export interface ApprovalRequest {
  id: string;
  source_type: string;
  source_id: string;
  title: string;
  change_class: string;
  required_level: string;
  status: string;
  packet: ReviewPacket | null;
  requested_by: string;
  decided_by: string | null;
  comment: string;
  created_at: string;
  decided_at: string | null;
}

export const Review = {
  packet: (workflowId: string) => api.get<ReviewPacket>(`/review/packet/${workflowId}`),
  approvals: () => api.get<ApprovalRequest[]>("/review/approvals"),
  approval: (id: string) => api.get<ApprovalRequest>(`/review/approvals/${id}`),
  requestApproval: (workflowId: string, inputs: Record<string, unknown> = {}) =>
    api.post<ApprovalRequest>("/review/approvals", { workflow_id: workflowId, inputs }),
  decide: (id: string, decision: string, comment = "") =>
    api.post<ApprovalRequest>(`/review/approvals/${id}/decision`, { decision, comment }),
};

// --- compliance & drift (v4.0 Pillar B) ----
export interface FieldDrift {
  field: string;
  desired: string;
  observed: string;
  state: string; // compliant | drifted | unknown
}
export interface ResourceDrift {
  resource: string;
  state: string;
  fields: FieldDrift[];
  reconcile_action: string;
}
export interface DriftReport {
  target: string;
  connector: string;
  action: string;
  status: string; // compliant | drifted | unknown
  drift_count: number;
  resources: ResourceDrift[];
  summary: string;
}
export interface DriftedItem {
  target: string;
  drift_count: number;
}
export interface PostureSnapshot {
  id: string;
  created_at: string;
  evaluated: number;
  compliant: number;
  drifted: number;
  drift_count: number;
  top_drifted: DriftedItem[];
  compliant_pct?: number;
}

export const Compliance = {
  posture: () => api.get<PostureSnapshot | null>("/compliance/posture"),
  history: () => api.get<PostureSnapshot[]>("/compliance/posture/history"),
  sweep: () => api.post<PostureSnapshot>("/compliance/sweep"),
  template: (id: string, answers: Record<string, unknown> = {}) =>
    api.post<DriftReport>(`/catalog/templates/${id}/compliance`, { survey_answers: answers }),
  workflow: (id: string) => api.post<DriftReport>(`/canvas/workflows/${id}/compliance`),
};

export const Cmdb = {
  schemas: () => api.get<CITypeSchema[]>("/cmdb/schemas"),
  schema: (t: string) => api.get<CITypeSchema>(`/cmdb/schemas/${t}`),
  saveSchema: (t: string, s: CITypeSchema) => api.put<CITypeSchema>(`/cmdb/schemas/${t}`, s),
  lineage: () => api.get<LineageSpec[]>("/cmdb/lineage"),
  lineageFor: (t: string) => api.get<LineageSpec>(`/cmdb/lineage/${t}`),
  saveLineage: (t: string, s: LineageSpec) => api.put<LineageSpec>(`/cmdb/lineage/${t}`, s),
  validateCi: (ci: Record<string, unknown>) => api.post<CIHealthReport>("/cmdb/validate-ci", ci),
  ciHealth: (name: string) => api.get<CIHealthReport>(`/cmdb/ci/${encodeURIComponent(name)}/health`),
};

export interface ServerThemeDoc {
  $schema: string;
  id: string;
  name: string;
  base: string;
  tokens: { light: Record<string, string>; dark: Record<string, string> };
  blurb?: string;
}

export const Themes = {
  list: () => api.get<{ themes: ServerThemeDoc[]; revision: number }>("/themes"),
  save: (doc: ServerThemeDoc) =>
    api.post<{ status: string; id: string; warnings: string[] }>("/themes", doc),
  remove: (id: string) => api.del<{ deleted: boolean }>(`/themes/${id}`),
};

// SSE stream of theme changes on the server volume (hot-reload). EventSource can't send headers,
// which is fine — the stream is non-sensitive presentational data and is unauthenticated.
export function openThemeStream(): EventSource {
  return new EventSource("/api/v1/themes/stream");
}

export interface PlatformStatus {
  app: string;
  version: string;
  environment: string;
  simulation_mode: boolean;
  scheduler_enabled: boolean;
  uptime_seconds: number;
  db_ok: boolean;
  workflows: number;
  jobs: number;
}

export const getHealth = () => api.get<Health>("/health");
export const getPlatformStatus = () => api.get<PlatformStatus>("/platform/status");
export const exportBundle = () => api.get<Record<string, unknown>>("/platform/export");

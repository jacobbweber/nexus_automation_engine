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

// Opens a WebSocket to a backend path (absolute, under /api/v1).
export function openSocket(path: string): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return new WebSocket(`${proto}://${window.location.host}/api/v1${path}`);
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

export interface Template {
  id: string;
  name: string;
  description: string;
  connector: string;
  action: string;
  markdown_documentation: string;
  supports_check_mode: boolean;
  supports_diff: boolean;
  survey: SurveyField[];
  default_params: Record<string, unknown>;
  owner: string;
  approval_state: string;
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
  created_at: string;
  updated_at: string;
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

export const Auth = {
  login: (username: string, password: string) =>
    api.post<LoginResponse>("/auth/login", { username, password }),
  me: () => api.get<User>("/auth/me"),
};

export const Catalog = {
  list: () => api.get<Template[]>("/catalog/templates"),
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

export const Connectors = {
  list: () => api.get<Capabilities[]>("/connectors"),
};

export const Canvas = {
  list: () => api.get<Workflow[]>("/canvas/workflows"),
  get: (id: string) => api.get<Workflow>(`/canvas/workflows/${id}`),
  save: (wf: { id?: string; name: string; description?: string; graph: WorkflowGraph }) =>
    api.post<Workflow>("/canvas/workflows", wf),
  remove: (id: string) => api.del<void>(`/canvas/workflows/${id}`),
  run: (id: string, inputs: Record<string, unknown>) =>
    api.post<{ run_id: string }>(`/canvas/workflows/${id}/run`, { inputs }),
  resolveApproval: (run_id: string, node_id: string, approved: boolean, response = "") =>
    api.post<{ resolved: boolean }>("/canvas/approvals/resolve", {
      run_id,
      node_id,
      approved,
      response,
    }),
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

export const getHealth = () => api.get<Health>("/health");

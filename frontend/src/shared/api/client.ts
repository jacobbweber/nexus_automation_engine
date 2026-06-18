// Thin API client. Uses relative paths so the Vite dev proxy and container
// networking both work without per-environment configuration.

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`/api/v1${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return (await res.json()) as T;
}

export interface Health {
  status: string;
  app: string;
  version: string;
  environment: string;
  simulation_mode: boolean;
}

export const getHealth = () => apiGet<Health>("/health");

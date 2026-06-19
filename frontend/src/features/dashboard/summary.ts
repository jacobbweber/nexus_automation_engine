// Pure fleet-pulse summary derived from the jobs list — counts, success rate, and average run
// duration. Status matching is case-insensitive so it's robust to backend casing.

import type { Job } from "@/shared/api/client";

export interface FleetSummary {
  total: number;
  running: number;
  pending: number;
  succeeded: number;
  failed: number;
  successRate: number | null; // 0..1 over finished (succeeded+failed); null if none finished
  avgDurationMs: number | null;
}

const SUCCEEDED = new Set(["completed", "success", "succeeded"]);
const PENDING = new Set(["pending", "queued"]);

export function summarizeJobs(jobs: Job[]): FleetSummary {
  let running = 0,
    pending = 0,
    succeeded = 0,
    failed = 0;
  let durSum = 0,
    durN = 0;

  for (const j of jobs) {
    const s = (j.status || "").toLowerCase();
    if (s === "running") running++;
    else if (PENDING.has(s)) pending++;
    else if (SUCCEEDED.has(s)) succeeded++;
    else if (s === "failed") failed++;

    if (j.started_at && j.finished_at) {
      const ms = Date.parse(j.finished_at) - Date.parse(j.started_at);
      if (Number.isFinite(ms) && ms >= 0) {
        durSum += ms;
        durN++;
      }
    }
  }

  const finished = succeeded + failed;
  return {
    total: jobs.length,
    running,
    pending,
    succeeded,
    failed,
    successRate: finished ? succeeded / finished : null,
    avgDurationMs: durN ? durSum / durN : null,
  };
}

export function formatDuration(ms: number | null): string {
  if (ms == null) return "—";
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return m < 60 ? `${m}m ${s % 60}s` : `${Math.floor(m / 60)}h ${m % 60}m`;
}

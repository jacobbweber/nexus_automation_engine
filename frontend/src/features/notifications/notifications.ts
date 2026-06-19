// Derives a non-blocking notifications feed from existing data (no new backend): open incidents,
// pending approvals, and recently finished runs. Pure mapping so it's unit-tested.

import type { Incident, Job, Workflow } from "@/shared/api/client";

export type NotifKind = "incident" | "approval" | "run";

export interface Notif {
  id: string;
  kind: NotifKind;
  title: string;
  detail: string;
  ts: string; // ISO timestamp for ordering
  to: string; // route to open
}

export function buildNotifications(
  incidentsByStatus: Record<string, Incident[]>,
  reviews: Workflow[],
  jobs: Job[],
): Notif[] {
  const out: Notif[] = [];

  for (const list of Object.values(incidentsByStatus)) {
    for (const inc of list) {
      if (inc.status === "resolved") continue;
      out.push({
        id: `incident:${inc.id}`,
        kind: "incident",
        title: `Incident: ${inc.title}`,
        detail: `${inc.severity} · ${inc.status}`,
        ts: inc.opened_at,
        to: "/incidents",
      });
    }
  }

  for (const wf of reviews) {
    out.push({
      id: `approval:${wf.id}`,
      kind: "approval",
      title: `Approval requested: ${wf.name}`,
      detail: `by ${wf.submitted_by ?? "?"}`,
      ts: wf.updated_at,
      to: "/governance",
    });
  }

  const finished = jobs
    .filter((j) => (j.status === "completed" || j.status === "failed") && j.finished_at)
    .sort((a, b) => (b.finished_at ?? "").localeCompare(a.finished_at ?? ""))
    .slice(0, 6);
  for (const j of finished) {
    out.push({
      id: `run:${j.id}`,
      kind: "run",
      title: `Run ${j.status}: ${j.name}`,
      detail: `${j.connector} · ${j.action}`,
      ts: j.finished_at ?? j.created_at,
      to: "/console",
    });
  }

  return out.sort((a, b) => (b.ts ?? "").localeCompare(a.ts ?? ""));
}

// Pure incident analytics (I37): top failing sources, MTTR, severity breakdown — computed from the
// board data (no new backend).

import type { Incident } from "@/shared/api/client";

export interface IncidentTrends {
  total: number;
  open: number;
  resolved: number;
  mttrMs: number | null; // mean time to resolution over resolved incidents
  topFailing: { label: string; count: number }[];
  bySeverity: Record<string, number>;
}

export function incidentTrends(all: Incident[]): IncidentTrends {
  let resolved = 0;
  let mttrSum = 0;
  let mttrN = 0;
  const byTitle = new Map<string, number>();
  const bySeverity: Record<string, number> = {};

  for (const inc of all) {
    bySeverity[inc.severity] = (bySeverity[inc.severity] ?? 0) + 1;
    byTitle.set(inc.title, (byTitle.get(inc.title) ?? 0) + 1);
    if (inc.status === "resolved" || inc.resolved_at) {
      resolved++;
      if (inc.resolved_at && inc.opened_at) {
        const ms = Date.parse(inc.resolved_at) - Date.parse(inc.opened_at);
        if (Number.isFinite(ms) && ms >= 0) {
          mttrSum += ms;
          mttrN++;
        }
      }
    }
  }

  const topFailing = [...byTitle.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  return {
    total: all.length,
    open: all.length - resolved,
    resolved,
    mttrMs: mttrN ? mttrSum / mttrN : null,
    topFailing,
    bySeverity,
  };
}

export function formatMttr(ms: number | null): string {
  if (ms == null) return "—";
  const m = Math.round(ms / 60000);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  return h < 24 ? `${h}h ${m % 60}m` : `${Math.floor(h / 24)}d ${h % 24}h`;
}

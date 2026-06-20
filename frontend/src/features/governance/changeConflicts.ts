// Pure helpers for the change calendar (J39): conflict detection + day grouping. A conflict is two
// changes whose time windows overlap AND touch at least one shared CI.

import type { ServiceNowChange } from "@/shared/api/client";

export interface Conflict {
  a: string;
  b: string;
  cis: string[];
}

function overlaps(a: ServiceNowChange, b: ServiceNowChange): boolean {
  return Date.parse(a.start) < Date.parse(b.end) && Date.parse(b.start) < Date.parse(a.end);
}

export function detectConflicts(changes: ServiceNowChange[]): Conflict[] {
  const out: Conflict[] = [];
  for (let i = 0; i < changes.length; i++) {
    for (let j = i + 1; j < changes.length; j++) {
      const a = changes[i];
      const b = changes[j];
      const shared = a.affected_cis.filter((c) => b.affected_cis.includes(c));
      if (shared.length > 0 && overlaps(a, b)) out.push({ a: a.number, b: b.number, cis: shared });
    }
  }
  return out;
}

/** Set of change numbers that participate in any conflict. */
export function conflictedNumbers(conflicts: Conflict[]): Set<string> {
  const s = new Set<string>();
  for (const c of conflicts) {
    s.add(c.a);
    s.add(c.b);
  }
  return s;
}

/** Group changes by local calendar day (sorted). */
export function groupByDay(changes: ServiceNowChange[]): [string, ServiceNowChange[]][] {
  const by = new Map<string, ServiceNowChange[]>();
  for (const c of [...changes].sort((a, b) => a.start.localeCompare(b.start))) {
    const day = new Date(c.start).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
    (by.get(day) ?? by.set(day, []).get(day)!).push(c);
  }
  return [...by.entries()];
}

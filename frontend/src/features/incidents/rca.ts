// RCA assist (I36): data + rules, no AI. Tags a failure mode from the incident text, finds similar
// past incidents (same title), and suggests a remediation reused from a similar resolved incident.

import type { Incident } from "@/shared/api/client";

const MODES: { tag: string; keywords: string[] }[] = [
  { tag: "timeout", keywords: ["timeout", "timed out", "deadline"] },
  { tag: "permission", keywords: ["permission", "denied", "unauthorized", "forbidden", "403"] },
  { tag: "connection", keywords: ["connection", "unreachable", "refused", "network", "dns"] },
  { tag: "validation", keywords: ["validation", "rejected", "invalid", "cmdb", "lifecycle"] },
  { tag: "approval", keywords: ["approval", "not approved", "change not"] },
  { tag: "capacity", keywords: ["capacity", "quota", "out of space", "resource"] },
];

export function failureMode(inc: Incident): string {
  const hay = `${inc.title} ${inc.summary}`.toLowerCase();
  for (const m of MODES) if (m.keywords.some((k) => hay.includes(k))) return m.tag;
  return "failure";
}

export interface Rca {
  similarCount: number;
  suggestedRemediationId: string | null;
}

export function rcaForIncident(inc: Incident, all: Incident[]): Rca {
  const similar = all.filter((x) => x.id !== inc.id && x.title === inc.title);
  const withRemediation =
    inc.remediation_workflow_id ? null : similar.find((x) => x.remediation_workflow_id)?.remediation_workflow_id ?? null;
  return { similarCount: similar.length, suggestedRemediationId: withRemediation };
}

import { describe, expect, it } from "vitest";
import type { Incident } from "@/shared/api/client";
import { failureMode, rcaForIncident } from "./rca";

const inc = (over: Partial<Incident>): Incident => ({
  id: "i", title: "Workflow failed: Patch", status: "new", severity: "high",
  source_type: "workflow", source_id: "w1", summary: "", assigned_to: null,
  remediation_workflow_id: null, opened_at: "2026-06-19T10:00:00Z", resolved_at: null, ...over,
});

describe("failureMode", () => {
  it("tags from title/summary keywords, defaulting to 'failure'", () => {
    expect(failureMode(inc({ summary: "connection refused to host" }))).toBe("connection");
    expect(failureMode(inc({ summary: "CMDB validation rejected the target" }))).toBe("validation");
    expect(failureMode(inc({ summary: "something unexpected" }))).toBe("failure");
  });
});

describe("rcaForIncident", () => {
  it("counts similar incidents (same title) and suggests a sibling's remediation", () => {
    const target = inc({ id: "1" });
    const all = [
      target,
      inc({ id: "2", remediation_workflow_id: "wf-fix" }),
      inc({ id: "3", title: "Other failure" }),
    ];
    const rca = rcaForIncident(target, all);
    expect(rca.similarCount).toBe(1); // only #2 shares the title
    expect(rca.suggestedRemediationId).toBe("wf-fix");
  });

  it("does not suggest a remediation when the incident already has one", () => {
    const target = inc({ id: "1", remediation_workflow_id: "own" });
    const rca = rcaForIncident(target, [target, inc({ id: "2", remediation_workflow_id: "wf-fix" })]);
    expect(rca.suggestedRemediationId).toBeNull();
  });
});

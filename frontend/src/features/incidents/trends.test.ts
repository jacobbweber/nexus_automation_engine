import { describe, expect, it } from "vitest";
import type { Incident } from "@/shared/api/client";
import { formatMttr, incidentTrends } from "./trends";

const inc = (over: Partial<Incident>): Incident => ({
  id: "i", title: "Workflow failed: Patch", status: "new", severity: "high",
  source_type: "workflow", source_id: "w1", summary: "", assigned_to: null,
  remediation_workflow_id: null, opened_at: "2026-06-19T10:00:00Z", resolved_at: null, ...over,
});

describe("incidentTrends", () => {
  it("counts open vs resolved and ranks top failing", () => {
    const t = incidentTrends([
      inc({ id: "1", title: "Workflow failed: Patch" }),
      inc({ id: "2", title: "Workflow failed: Patch", status: "resolved", resolved_at: "2026-06-19T10:30:00Z" }),
      inc({ id: "3", title: "Workflow failed: Backup" }),
    ]);
    expect(t.total).toBe(3);
    expect(t.resolved).toBe(1);
    expect(t.open).toBe(2);
    expect(t.topFailing[0]).toEqual({ label: "Workflow failed: Patch", count: 2 });
  });

  it("computes MTTR over resolved incidents only", () => {
    const t = incidentTrends([
      inc({ id: "1", status: "resolved", opened_at: "2026-06-19T10:00:00Z", resolved_at: "2026-06-19T10:30:00Z" }),
      inc({ id: "2", status: "new" }),
    ]);
    expect(t.mttrMs).toBe(30 * 60 * 1000);
  });

  it("returns null MTTR with no resolved incidents", () => {
    expect(incidentTrends([inc({})]).mttrMs).toBeNull();
  });
});

describe("formatMttr", () => {
  it("formats null / minutes / hours", () => {
    expect(formatMttr(null)).toBe("—");
    expect(formatMttr(20 * 60000)).toBe("20m");
    expect(formatMttr(90 * 60000)).toBe("1h 30m");
  });
});

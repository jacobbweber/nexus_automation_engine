import { describe, expect, it } from "vitest";
import type { Incident, Job, Workflow } from "@/shared/api/client";
import { buildNotifications } from "./notifications";

const incident = (over: Partial<Incident>): Incident => ({
  id: "i1", title: "DB down", status: "new", severity: "high", source_type: "workflow",
  source_id: "w1", summary: "", assigned_to: null, remediation_workflow_id: null,
  opened_at: "2026-06-19T10:00:00Z", resolved_at: null, ...over,
});
const wf = (over: Partial<Workflow>): Workflow => ({
  id: "w1", name: "Patch", description: "", graph: { nodes: [], edges: [], viewport: {} },
  review_state: "submitted", submitted_by: "alice", reviewed_by: null, owner: "alice", team: "Ops",
  tags: [], created_at: "2026-06-19T09:00:00Z", updated_at: "2026-06-19T11:00:00Z", ...over,
});
const job = (over: Partial<Job>): Job => ({
  id: "j1", name: "Deploy", connector: "ansible", action: "run", status: "completed",
  initiated_by: "bob", created_at: "2026-06-19T08:00:00Z", started_at: "2026-06-19T08:01:00Z",
  finished_at: "2026-06-19T08:05:00Z", error_message: null, ...over,
});

describe("buildNotifications", () => {
  it("includes open incidents but skips resolved ones", () => {
    const n = buildNotifications(
      { new: [incident({})], resolved: [incident({ id: "i2", status: "resolved" })] },
      [],
      [],
    );
    expect(n.map((x) => x.id)).toEqual(["incident:i1"]);
    expect(n[0].to).toBe("/incidents");
  });

  it("includes pending approvals and finished runs, ordered by recency", () => {
    const n = buildNotifications({}, [wf({})], [job({})]);
    const ids = n.map((x) => x.id);
    expect(ids).toContain("approval:w1");
    expect(ids).toContain("run:j1");
    // approval updated 11:00 is newer than run finished 08:05
    expect(ids[0]).toBe("approval:w1");
  });

  it("ignores still-running jobs", () => {
    const n = buildNotifications({}, [], [job({ id: "j9", status: "running", finished_at: null })]);
    expect(n).toHaveLength(0);
  });
});

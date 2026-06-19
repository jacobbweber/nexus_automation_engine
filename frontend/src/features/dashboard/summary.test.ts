import { describe, expect, it } from "vitest";
import type { Job } from "@/shared/api/client";
import { formatDuration, summarizeJobs } from "./summary";

const job = (over: Partial<Job>): Job => ({
  id: "j", name: "n", connector: "ansible", action: "run", status: "completed",
  initiated_by: "u", created_at: "2026-06-19T08:00:00Z", started_at: null, finished_at: null,
  error_message: null, ...over,
});

describe("summarizeJobs", () => {
  it("counts by status case-insensitively", () => {
    const s = summarizeJobs([
      job({ status: "RUNNING" }),
      job({ status: "completed" }),
      job({ status: "Failed" }),
      job({ status: "queued" }),
    ]);
    expect(s.total).toBe(4);
    expect(s.running).toBe(1);
    expect(s.succeeded).toBe(1);
    expect(s.failed).toBe(1);
    expect(s.pending).toBe(1);
  });

  it("computes success rate over finished runs only", () => {
    const s = summarizeJobs([
      job({ status: "completed" }),
      job({ status: "completed" }),
      job({ status: "failed" }),
      job({ status: "running" }),
    ]);
    expect(s.successRate).toBeCloseTo(2 / 3, 5);
  });

  it("returns null success rate when nothing has finished", () => {
    expect(summarizeJobs([job({ status: "running" })]).successRate).toBeNull();
  });

  it("averages duration from started/finished timestamps", () => {
    const s = summarizeJobs([
      job({ started_at: "2026-06-19T08:00:00Z", finished_at: "2026-06-19T08:02:00Z" }),
      job({ started_at: "2026-06-19T08:00:00Z", finished_at: "2026-06-19T08:04:00Z" }),
    ]);
    expect(s.avgDurationMs).toBe(180000); // mean of 2m and 4m = 3m
  });
});

describe("formatDuration", () => {
  it("formats null, seconds, minutes", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(45000)).toBe("45s");
    expect(formatDuration(125000)).toBe("2m 5s");
  });
});

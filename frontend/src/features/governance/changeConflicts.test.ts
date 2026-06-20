import { describe, expect, it } from "vitest";
import type { ServiceNowChange } from "@/shared/api/client";
import { conflictedNumbers, detectConflicts } from "./changeConflicts";

const chg = (number: string, start: string, end: string, cis: string[]): ServiceNowChange => ({
  number, short_description: "x", state: "scheduled", start, end,
  assignment_group: "Ops", risk: "high", affected_cis: cis,
});

describe("detectConflicts", () => {
  it("flags overlapping windows that share a CI", () => {
    const a = chg("A", "2026-06-20T22:00:00Z", "2026-06-21T02:00:00Z", ["db-prod-01"]);
    const b = chg("B", "2026-06-21T00:00:00Z", "2026-06-21T03:00:00Z", ["db-prod-01", "web-prod-01"]);
    const conflicts = detectConflicts([a, b]);
    expect(conflicts).toHaveLength(1);
    expect(conflicts[0].cis).toEqual(["db-prod-01"]);
    expect(conflictedNumbers(conflicts)).toEqual(new Set(["A", "B"]));
  });

  it("does not flag overlapping windows with no shared CI", () => {
    const a = chg("A", "2026-06-20T22:00:00Z", "2026-06-21T02:00:00Z", ["db-prod-01"]);
    const b = chg("B", "2026-06-20T23:00:00Z", "2026-06-21T01:00:00Z", ["web-prod-02"]);
    expect(detectConflicts([a, b])).toHaveLength(0);
  });

  it("does not flag a shared CI when windows don't overlap", () => {
    const a = chg("A", "2026-06-20T22:00:00Z", "2026-06-20T23:00:00Z", ["db-prod-01"]);
    const b = chg("B", "2026-06-21T00:00:00Z", "2026-06-21T01:00:00Z", ["db-prod-01"]);
    expect(detectConflicts([a, b])).toHaveLength(0);
  });
});

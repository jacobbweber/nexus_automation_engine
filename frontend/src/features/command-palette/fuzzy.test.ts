import { describe, expect, it } from "vitest";
import { fuzzyMatch, rank } from "./fuzzy";

describe("fuzzyMatch", () => {
  it("returns 0 for an empty query and null for a non-subsequence", () => {
    expect(fuzzyMatch("", "anything")).toBe(0);
    expect(fuzzyMatch("xyz", "catalog")).toBeNull();
  });

  it("matches subsequences and rewards start + contiguous hits", () => {
    expect(fuzzyMatch("cat", "catalog")).not.toBeNull();
    // a prefix/contiguous match should outscore a scattered one
    const contiguous = fuzzyMatch("can", "canvas")!;
    const scattered = fuzzyMatch("cns", "canvas")!;
    expect(contiguous).toBeGreaterThan(scattered);
  });
});

describe("rank", () => {
  const items = [
    { label: "Canvas", keywords: "workflow builder" },
    { label: "Catalog", keywords: "templates" },
    { label: "Incidents", keywords: "failures" },
  ];

  it("returns all items unfiltered for an empty query", () => {
    expect(rank(items, "")).toHaveLength(3);
  });

  it("filters + orders by relevance", () => {
    const r = rank(items, "cat");
    expect(r[0].label).toBe("Catalog");
    expect(r.find((i) => i.label === "Incidents")).toBeUndefined();
  });

  it("matches via keywords too", () => {
    const r = rank(items, "builder");
    expect(r[0].label).toBe("Canvas");
  });
});

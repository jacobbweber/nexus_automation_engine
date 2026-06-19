import { describe, expect, it } from "vitest";
import { toggleId } from "./favorites";

describe("toggleId", () => {
  it("adds an id that isn't present", () => {
    expect(toggleId(["a"], "b")).toEqual(["a", "b"]);
  });
  it("removes an id that is present", () => {
    expect(toggleId(["a", "b"], "a")).toEqual(["b"]);
  });
  it("is its own inverse", () => {
    const once = toggleId([], "x");
    expect(toggleId(once, "x")).toEqual([]);
  });
});

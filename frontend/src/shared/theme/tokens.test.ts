import { describe, expect, it } from "vitest";
import { SEMANTIC_TOKENS, motion, radius, space } from "./tokens";

describe("token foundation", () => {
  it("exposes the spacing scale on a 4px grid", () => {
    expect(space.s1).toBe(4);
    expect(space.s4).toBe(16);
    expect(space.s8).toBe(64);
  });

  it("exposes the radius ramp", () => {
    expect(radius.md).toBe(14);
    expect(radius.lg).toBe(20);
    expect(radius.pill).toBeGreaterThan(1000);
  });

  it("exposes calm decelerating motion durations", () => {
    expect(motion.dur1).toBeLessThan(motion.dur5);
    expect(motion.easeOut).toContain("cubic-bezier");
  });

  it("declares the protected run-status tokens in the contract", () => {
    for (const t of ["--run-running", "--run-ok", "--run-warn", "--run-failed", "--run-skipped"]) {
      expect(SEMANTIC_TOKENS).toContain(t);
    }
  });

  it("declares core surface/text/accent tokens", () => {
    for (const t of ["--bg", "--surface", "--text", "--accent", "--border", "--focus"]) {
      expect(SEMANTIC_TOKENS).toContain(t);
    }
  });
});

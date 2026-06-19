import { describe, expect, it } from "vitest";
import { validateTheme } from "../theme-schema";
import { BUILTIN_THEMES, DEFAULT_THEME_ID } from "./builtins";

describe("built-in themes", () => {
  it("ships 10 themes with unique ids incl. the default", () => {
    expect(BUILTIN_THEMES).toHaveLength(10);
    const ids = BUILTIN_THEMES.map((t) => t.id);
    expect(new Set(ids).size).toBe(10);
    expect(ids).toContain(DEFAULT_THEME_ID);
  });

  it.each(BUILTIN_THEMES.map((t) => [t.id, t] as const))(
    "%s passes the deterministic validator (shape + allow-list + AA contrast)",
    (_id, theme) => {
      const r = validateTheme(theme);
      expect(r.errors, r.errors.join("\n")).toEqual([]);
      expect(r.ok).toBe(true);
    },
  );

  it("covers the required spread (neutral, minimalist, dark, ADHD, AAA, playful)", () => {
    const ids = BUILTIN_THEMES.map((t) => t.id);
    for (const must of ["signal", "paper", "midnight-ops", "focus-flow", "calm-clarity", "high-contrast", "terminal"]) {
      expect(ids).toContain(must);
    }
  });
});

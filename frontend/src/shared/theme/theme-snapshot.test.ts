// Token regression matrix (L46): snapshot every built-in theme's generated CSS (light + dark token
// maps) so any unintended palette/token change is caught in CI. Pairs with contrast.test.ts (which
// gates the *quality* of changes) — this gates *unintended* ones across the theme × mode matrix.

import { describe, expect, it } from "vitest";
import { themeCss } from "./theme-apply";
import { BUILTIN_THEMES } from "./themes/builtins";
import { validateTheme } from "./theme-schema";

describe("theme token regression matrix", () => {
  it.each(BUILTIN_THEMES.map((t) => [t.id, t] as const))(
    "%s theme tokens are stable (light + dark)",
    (_id, theme) => {
      expect(themeCss(theme)).toMatchSnapshot();
    },
  );

  it("every theme declares both light and dark token maps", () => {
    for (const t of BUILTIN_THEMES) {
      expect(Object.keys(t.tokens.light).length).toBeGreaterThan(10);
      expect(Object.keys(t.tokens.dark).length).toBeGreaterThan(10);
    }
  });

  // Locks in the run-status distinguishability fix: no built-in may ship a run-status hue collision
  // (e.g. amber --run-warn vs a warm --run-skipped) in either mode.
  it("every built-in theme validates with zero warnings", () => {
    for (const t of BUILTIN_THEMES) {
      const r = validateTheme(t);
      expect(r.ok, `${t.id}: ${r.errors.join(", ")}`).toBe(true);
      expect(r.warnings, `${t.id}: ${r.warnings.join(", ")}`).toEqual([]);
    }
  });
});

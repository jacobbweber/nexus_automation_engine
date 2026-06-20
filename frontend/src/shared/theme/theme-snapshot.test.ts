// Token regression matrix (L46): snapshot every built-in theme's generated CSS (light + dark token
// maps) so any unintended palette/token change is caught in CI. Pairs with contrast.test.ts (which
// gates the *quality* of changes) — this gates *unintended* ones across the theme × mode matrix.

import { describe, expect, it } from "vitest";
import { themeCss } from "./theme-apply";
import { BUILTIN_THEMES } from "./themes/builtins";

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
});

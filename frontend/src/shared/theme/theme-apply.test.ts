import { describe, expect, it } from "vitest";
import { themeCss } from "./theme-apply";
import { BUILTIN_THEMES } from "./themes/builtins";

describe("themeCss", () => {
  const ember = BUILTIN_THEMES.find((t) => t.id === "ember")!;

  it("emits an @layer theme block scoped by data-theme, with a dark override selector", () => {
    const css = themeCss(ember);
    expect(css.startsWith("@layer theme {")).toBe(true);
    expect(css).toContain('[data-theme="ember"]{');
    expect(css).toContain('[data-mode="dark"][data-theme="ember"]{');
    expect(css).toContain("--bg:");
  });

  it("includes the theme's actual token values", () => {
    const css = themeCss(ember);
    expect(css).toContain(ember.tokens.light["--accent"]);
    expect(css).toContain(ember.tokens.dark["--bg"]);
  });
});

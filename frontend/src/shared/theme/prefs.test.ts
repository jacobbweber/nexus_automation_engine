import { describe, expect, it } from "vitest";
import { DEFAULT_PREFS, applyPrefs, clampScale, type PrefsState } from "./prefs-core";

describe("prefs core", () => {
  it("defaults to cozy / no-dyslexia / 100%", () => {
    expect(DEFAULT_PREFS.density).toBe("cozy");
    expect(DEFAULT_PREFS.dyslexia).toBe(false);
    expect(DEFAULT_PREFS.textScale).toBe(100);
  });

  it("clamps text scale into the 90–140 range", () => {
    expect(clampScale(50)).toBe(90);
    expect(clampScale(200)).toBe(140);
    expect(clampScale(115)).toBe(115);
    expect(clampScale(NaN)).toBe(100);
  });

  it("applies attributes + root font-size to the document root", () => {
    const root = document.createElement("html");
    const state: PrefsState = { density: "compact", dyslexia: true, textScale: 120 };
    applyPrefs(state, root);
    expect(root.dataset.density).toBe("compact");
    expect(root.dataset.dyslexia).toBe("on");
    expect(root.style.fontSize).toBe("120%");
  });

  it("leaves font-size unset at 100% so rem stays native", () => {
    const root = document.createElement("html");
    applyPrefs({ density: "cozy", dyslexia: false, textScale: 100 }, root);
    expect(root.style.fontSize).toBe("");
  });
});

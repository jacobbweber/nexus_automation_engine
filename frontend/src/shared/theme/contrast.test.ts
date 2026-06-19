import { describe, expect, it } from "vitest";
import { AA_LARGE, AA_NORMAL, contrastRatio, meetsAA } from "./contrast";

// Resolved Signal (default theme) palette — mirrors the primitives/semantic values in tokens.css.
// This is the deterministic A7 gate: if a palette change regresses contrast, CI fails here.
const light = {
  bg: "#fbf7f2",
  surface: "#ffffff",
  text: "#1a1714",
  textMuted: "#7d6a57",
  accent: "#2f72b0",
  accentContrast: "#ffffff",
  run: { running: "#2f72b0", ok: "#4c8a5e", warn: "#b07a1e", failed: "#b23a33", skipped: "#8a7f72" },
};
const dark = {
  bg: "#141210",
  surface: "#201d1a",
  text: "#fbf7f2",
  textMuted: "#c8b6a0",
  accent: "#6ba6db",
  accentContrast: "#141210",
  run: { running: "#6ba6db", ok: "#8fc7a1", warn: "#e0bd6f", failed: "#e08a82", skipped: "#a8927a" },
};

describe.each([
  ["light", light],
  ["dark", dark],
])("Signal palette (%s) — WCAG AA", (_name, p) => {
  it("body & muted text clear AA-normal on bg and surface", () => {
    expect(meetsAA(p.text, p.bg)).toBe(true);
    expect(meetsAA(p.text, p.surface)).toBe(true);
    expect(meetsAA(p.textMuted, p.bg)).toBe(true);
    expect(meetsAA(p.textMuted, p.surface)).toBe(true);
  });

  it("accent-contrast text clears AA-normal on the accent (primary buttons)", () => {
    expect(contrastRatio(p.accentContrast, p.accent)).toBeGreaterThanOrEqual(AA_NORMAL);
  });

  it("accent clears AA-normal on bg (links/icons)", () => {
    expect(meetsAA(p.accent, p.bg)).toBe(true);
  });

  it("every run-status color clears AA-large on bg (status icons are graphics)", () => {
    for (const [name, color] of Object.entries(p.run)) {
      const r = contrastRatio(color, p.bg);
      expect(r, `${name} ${r.toFixed(2)} < ${AA_LARGE}`).toBeGreaterThanOrEqual(AA_LARGE);
    }
  });
});

describe("contrast util sanity", () => {
  it("black/white is ~21:1 and identical colors are 1:1", () => {
    expect(Math.round(contrastRatio("#000000", "#ffffff"))).toBe(21);
    expect(contrastRatio("#445566", "#445566")).toBeCloseTo(1, 5);
  });
});

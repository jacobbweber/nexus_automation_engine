import { describe, expect, it } from "vitest";
import { contrastRatio, meetsAA } from "./contrast";
import { THEME_SCHEMA, type ThemeDoc, nudgeForContrast, validateTheme } from "./theme-schema";

function validTheme(): ThemeDoc {
  const light = {
    "--bg": "#fbf7f2", "--surface": "#ffffff", "--surface-2": "#f4ece1",
    "--text": "#1a1714", "--text-muted": "#7d6a57", "--border": "#e0d3c1",
    "--accent": "#2f72b0", "--accent-hover": "#285f93", "--accent-contrast": "#ffffff",
    "--success": "#4c8a5e", "--warn": "#b07a1e", "--danger": "#b23a33", "--info": "#3e6e8e",
    "--run-running": "#2f72b0", "--run-ok": "#4c8a5e", "--run-warn": "#b07a1e",
    "--run-failed": "#b23a33", "--run-skipped": "#8a7f72", "--focus": "#2f72b0",
  };
  const dark = {
    "--bg": "#141210", "--surface": "#201d1a", "--surface-2": "#262220",
    "--text": "#fbf7f2", "--text-muted": "#c8b6a0", "--border": "#352f2a",
    "--accent": "#6ba6db", "--accent-hover": "#9cc6ec", "--accent-contrast": "#141210",
    "--success": "#8fc7a1", "--warn": "#e0bd6f", "--danger": "#e08a82", "--info": "#8fbdd6",
    "--run-running": "#6ba6db", "--run-ok": "#8fc7a1", "--run-warn": "#e0bd6f",
    "--run-failed": "#e08a82", "--run-skipped": "#a8927a", "--focus": "#6ba6db",
  };
  return { $schema: THEME_SCHEMA, id: "demo", name: "Demo", base: "light", tokens: { light, dark } };
}

describe("validateTheme", () => {
  it("accepts a well-formed AA-passing theme", () => {
    const r = validateTheme(validTheme());
    expect(r.errors).toEqual([]);
    expect(r.ok).toBe(true);
  });

  it("rejects a wrong $schema", () => {
    const t = { ...validTheme(), $schema: "something-else" };
    expect(validateTheme(t).ok).toBe(false);
  });

  it("rejects a missing required token", () => {
    const t = validTheme();
    delete (t.tokens.light as Record<string, string>)["--text"];
    const r = validateTheme(t);
    expect(r.ok).toBe(false);
    expect(r.errors.some((e) => e.includes("--text"))).toBe(true);
  });

  it("rejects a disallowed key (layout/spacing/CSS injection attempt)", () => {
    const t = validTheme();
    (t.tokens.light as Record<string, string>)["--space-4"] = "#fff";
    const r = validateTheme(t);
    expect(r.ok).toBe(false);
    expect(r.errors.some((e) => e.includes("disallowed"))).toBe(true);
  });

  it("rejects an invalid color value", () => {
    const t = validTheme();
    (t.tokens.light as Record<string, string>)["--accent"] = "blue";
    expect(validateTheme(t).ok).toBe(false);
  });

  it("rejects an inaccessible (low-contrast) theme", () => {
    const t = validTheme();
    t.tokens.light["--text"] = "#f6f1ea"; // ~bg, fails AA
    const r = validateTheme(t);
    expect(r.ok).toBe(false);
    expect(r.errors.some((e) => e.toLowerCase().includes("aa"))).toBe(true);
  });
});

describe("nudgeForContrast", () => {
  it("pushes a failing fg until it clears AA on the bg", () => {
    const fixed = nudgeForContrast("#8aa6c0", "#ffffff"); // starts well under 4.5 on white
    expect(meetsAA(fixed, "#ffffff")).toBe(true);
    expect(contrastRatio(fixed, "#ffffff")).toBeGreaterThanOrEqual(4.5);
  });
});

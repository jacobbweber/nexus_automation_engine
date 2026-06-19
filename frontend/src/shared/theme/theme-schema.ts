// nexus-theme/v1 — the theme contract + deterministic validator (B9/B10).
//
// A theme is DATA: it may only remap an allow-listed set of semantic tokens for light + dark. It
// can never contain selectors, layout, spacing, or fonts. The validator is the sole safety gate
// (no AI anywhere — ADR-0008): it checks shape, the key allow-list, completeness, valid colors,
// WCAG-AA contrast, and protected-status distinguishability. Built on contrast.ts.

import { AA_LARGE, AA_NORMAL, contrastRatio, hsl, hueDistance, isHex, meetsAA } from "./contrast";

export const THEME_SCHEMA = "nexus-theme/v1";

export interface ThemeDoc {
  $schema: string;
  id: string;
  name: string;
  author?: string;
  version?: string;
  base: "light" | "dark";
  personality?: { radius?: string; density?: string; motion?: string };
  tokens: { light: Record<string, string>; dark: Record<string, string> };
  a11y?: Record<string, unknown>;
}

// Every token key a theme is allowed to set. Anything outside this set is rejected (this is what
// blocks layout/spacing/selector/CSS injection attempts).
export const ALLOWED_TOKEN_KEYS = new Set<string>([
  "--bg", "--surface", "--surface-2", "--surface-3", "--overlay",
  "--text", "--text-muted", "--text-subtle", "--text-onAccent",
  "--border", "--border-strong", "--divider",
  "--accent", "--accent-hover", "--accent-active", "--accent-contrast", "--accent-soft",
  "--success", "--warn", "--danger", "--info",
  "--run-running", "--run-ok", "--run-warn", "--run-failed", "--run-skipped",
  "--focus", "--selection", "--link",
]);

// Keys that MUST be present (both modes) — the legibility-critical contract.
export const REQUIRED_TOKEN_KEYS = [
  "--bg", "--surface", "--surface-2", "--text", "--text-muted", "--border",
  "--accent", "--accent-hover", "--accent-contrast",
  "--success", "--warn", "--danger", "--info",
  "--run-running", "--run-ok", "--run-warn", "--run-failed", "--run-skipped", "--focus",
] as const;

const RUN_KEYS = ["--run-running", "--run-ok", "--run-warn", "--run-failed", "--run-skipped"] as const;

export interface ValidationResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
}

function validateMode(mode: "light" | "dark", t: Record<string, string>, out: ValidationResult) {
  // allow-list + valid colors
  for (const [k, v] of Object.entries(t)) {
    if (!ALLOWED_TOKEN_KEYS.has(k)) {
      out.errors.push(`${mode}: disallowed token "${k}" (themes may only set semantic color tokens)`);
      continue;
    }
    if (!isHex(v)) out.errors.push(`${mode}: "${k}" is not a valid hex color ("${String(v)}")`);
  }
  // completeness
  for (const k of REQUIRED_TOKEN_KEYS) {
    if (!(k in t)) out.errors.push(`${mode}: missing required token "${k}"`);
  }
  // a11y contrast (only when the needed keys are valid hex)
  const ok = (k: string) => isHex(t[k]);
  if (ok("--text") && ok("--bg") && !meetsAA(t["--text"], t["--bg"]))
    out.errors.push(`${mode}: body text fails AA on bg (${contrastRatio(t["--text"], t["--bg"]).toFixed(2)})`);
  if (ok("--text") && ok("--surface") && !meetsAA(t["--text"], t["--surface"]))
    out.errors.push(`${mode}: body text fails AA on surface`);
  if (ok("--text-muted") && ok("--bg") && !meetsAA(t["--text-muted"], t["--bg"]))
    out.errors.push(`${mode}: muted text fails AA on bg (${contrastRatio(t["--text-muted"], t["--bg"]).toFixed(2)})`);
  if (ok("--accent-contrast") && ok("--accent") && !meetsAA(t["--accent-contrast"], t["--accent"]))
    out.errors.push(`${mode}: accent-contrast fails AA on accent (primary buttons)`);
  for (const k of RUN_KEYS) {
    if (ok(k) && ok("--bg") && contrastRatio(t[k], t["--bg"]) < AA_LARGE)
      out.errors.push(`${mode}: ${k} fails AA-large on bg (${contrastRatio(t[k], t["--bg"]).toFixed(2)})`);
  }
  // protected-status distinguishability (hue separation; icons also disambiguate, hence a warning)
  for (let i = 0; i < RUN_KEYS.length; i++) {
    for (let j = i + 1; j < RUN_KEYS.length; j++) {
      const a = t[RUN_KEYS[i]], b = t[RUN_KEYS[j]];
      if (isHex(a) && isHex(b)) {
        const sa = hsl(a), sb = hsl(b);
        if (sa.s > 0.15 && sb.s > 0.15 && hueDistance(sa.h, sb.h) < 18)
          out.warnings.push(`${mode}: ${RUN_KEYS[i]} and ${RUN_KEYS[j]} share a hue — statuses may be hard to tell apart`);
      }
    }
  }
}

/** Deterministically validate a candidate theme document. */
export function validateTheme(candidate: unknown): ValidationResult {
  const out: ValidationResult = { ok: false, errors: [], warnings: [] };
  if (typeof candidate !== "object" || candidate === null) {
    out.errors.push("theme must be an object");
    return out;
  }
  const c = candidate as Partial<ThemeDoc>;
  if (c.$schema !== THEME_SCHEMA) out.errors.push(`$schema must be "${THEME_SCHEMA}"`);
  if (!c.id || typeof c.id !== "string") out.errors.push("missing id");
  if (!c.name || typeof c.name !== "string") out.errors.push("missing name");
  if (c.base !== "light" && c.base !== "dark") out.errors.push('base must be "light" or "dark"');
  if (!c.tokens || typeof c.tokens !== "object") {
    out.errors.push("missing tokens");
    return out;
  }
  if (!c.tokens.light || typeof c.tokens.light !== "object") out.errors.push("missing tokens.light");
  else validateMode("light", c.tokens.light, out);
  if (!c.tokens.dark || typeof c.tokens.dark !== "object") out.errors.push("missing tokens.dark");
  else validateMode("dark", c.tokens.dark, out);

  out.ok = out.errors.length === 0;
  return out;
}

/** Best-effort auto-nudge: lighten/darken a fg until it meets the target ratio on bg (or give up). */
export function nudgeForContrast(fg: string, bg: string, large = false): string {
  const target = large ? AA_LARGE : AA_NORMAL;
  if (contrastRatio(fg, bg) >= target) return fg;
  const { h, s } = hsl(bg);
  // move fg toward black or white depending on which the bg is farther from
  const goDark = hsl(bg).l > 0.5;
  let best = fg;
  for (let step = 1; step <= 20; step++) {
    const l = goDark ? Math.max(0, 0.5 - step * 0.025) : Math.min(1, 0.5 + step * 0.025);
    const cand = hslToHex(h, s, l);
    if (contrastRatio(cand, bg) >= target) return cand;
    best = cand;
  }
  return best;
}

function hslToHex(h: number, s: number, l: number): string {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  let r = 0, g = 0, b = 0;
  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];
  const to = (n: number) => Math.round((n + m) * 255).toString(16).padStart(2, "0");
  return `#${to(r)}${to(g)}${to(b)}`;
}

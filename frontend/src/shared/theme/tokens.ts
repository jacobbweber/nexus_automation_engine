// Token constants for non-CSS consumers (canvas SVG geometry, charts, tests).
//
// These mirror the scales in tokens.css so canvas/SVG rendering can't drift from the stylesheet.
// Colors are NOT duplicated here — runtime color comes from the cascade; use cssVar() to read a
// resolved semantic token when SVG needs an actual value (it then honors mode/area/theme).

export const space = {
  s1: 4,
  s2: 8,
  s3: 12,
  s4: 16,
  s5: 24,
  s6: 32,
  s7: 48,
  s8: 64,
} as const;

export const radius = {
  xs: 6,
  sm: 10,
  md: 14,
  lg: 20,
  xl: 28,
  xl2: 36,
  pill: 9999,
} as const;

export const motion = {
  dur1: 120,
  dur2: 180,
  dur3: 240,
  dur4: 360,
  dur5: 520,
  easeOut: "cubic-bezier(.2,.8,.2,1)",
  easeSpring: "cubic-bezier(.34,1.56,.64,1)",
} as const;

// Semantic token keys components may consume (the contract). Kept as a list so tooling/tests can
// assert components only reference these.
export const SEMANTIC_TOKENS = [
  "--bg", "--surface", "--surface-2", "--surface-3", "--overlay",
  "--text", "--text-muted", "--text-subtle", "--text-onAccent",
  "--border", "--border-strong", "--divider",
  "--accent", "--accent-hover", "--accent-active", "--accent-contrast", "--accent-soft",
  "--success", "--warn", "--danger", "--info",
  "--run-running", "--run-ok", "--run-warn", "--run-failed", "--run-skipped",
  "--focus", "--selection", "--link",
  "--area-accent", "--area-tint",
] as const;

export type SemanticToken = (typeof SEMANTIC_TOKENS)[number];

/** Read a resolved CSS custom property (honors the active mode/area/theme). SSR/test-safe. */
export function cssVar(name: SemanticToken | string, el?: Element): string {
  if (typeof window === "undefined" || typeof getComputedStyle === "undefined") return "";
  const target = el ?? document.documentElement;
  return getComputedStyle(target).getPropertyValue(name).trim();
}

export type Mode = "system" | "light" | "dark";
export type Density = "cozy" | "comfortable" | "compact";

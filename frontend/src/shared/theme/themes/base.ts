// Complete, WCAG-AA-validated base token maps (the Signal default), plus a builder that produces a
// full nexus-theme/v1 doc from a small set of per-theme overrides. Themes that don't override a key
// inherit the base value — so every built-in theme is complete and AA-correct by construction, and
// each is still run through validateTheme() in the tests as the real gate.

import type { ThemeDoc } from "../theme-schema";
import { THEME_SCHEMA } from "../theme-schema";

export type Tokens = Record<string, string>;

export const BASE_LIGHT: Tokens = {
  "--bg": "#fbf7f2", "--surface": "#ffffff", "--surface-2": "#f4ece1", "--surface-3": "#ece2d4",
  "--text": "#1a1714", "--text-muted": "#7d6a57", "--text-subtle": "#a8927a",
  "--border": "#e0d3c1", "--border-strong": "#c8b6a0", "--divider": "#ece2d4",
  "--accent": "#2f72b0", "--accent-hover": "#285f93", "--accent-active": "#214e78", "--accent-contrast": "#ffffff",
  "--success": "#4c8a5e", "--warn": "#b07a1e", "--danger": "#b23a33", "--info": "#3e6e8e",
  "--run-running": "#2f72b0", "--run-ok": "#4c8a5e", "--run-warn": "#b07a1e",
  "--run-failed": "#b23a33", "--run-skipped": "#8a7f72",
  "--focus": "#2f72b0", "--link": "#285f93",
};

export const BASE_DARK: Tokens = {
  "--bg": "#141210", "--surface": "#201d1a", "--surface-2": "#262220", "--surface-3": "#352f2a",
  "--text": "#fbf7f2", "--text-muted": "#c8b6a0", "--text-subtle": "#a8927a",
  "--border": "#352f2a", "--border-strong": "#47403a", "--divider": "#262220",
  "--accent": "#6ba6db", "--accent-hover": "#9cc6ec", "--accent-active": "#9cc6ec", "--accent-contrast": "#141210",
  "--success": "#8fc7a1", "--warn": "#e0bd6f", "--danger": "#e08a82", "--info": "#8fbdd6",
  "--run-running": "#6ba6db", "--run-ok": "#8fc7a1", "--run-warn": "#e0bd6f",
  // Skipped is a desaturated cool gray so it never reads as amber next to --run-warn (status
  // distinguishability — the theme validator flags warm-skipped vs amber-warn hue collisions).
  "--run-failed": "#e08a82", "--run-skipped": "#8f949c",
  "--focus": "#6ba6db", "--link": "#9cc6ec",
};

export interface ThemeMeta {
  id: string;
  name: string;
  base: "light" | "dark";
  blurb: string; // short description for the picker
}

export function buildTheme(meta: ThemeMeta, light: Tokens = {}, dark: Tokens = {}): ThemeDoc & { blurb: string } {
  return {
    $schema: THEME_SCHEMA,
    id: meta.id,
    name: meta.name,
    base: meta.base,
    blurb: meta.blurb,
    tokens: {
      light: { ...BASE_LIGHT, ...light },
      dark: { ...BASE_DARK, ...dark },
    },
  };
}

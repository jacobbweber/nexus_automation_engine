// Pure display/accessibility preference logic + types (no React). Drives the density + a11y
// layers from tokens.css via data-attributes + a root font-size scale.

import type { Density } from "./tokens";

export interface PrefsState {
  density: Density; // cozy | comfortable | compact
  dyslexia: boolean; // swaps --font-ui to Atkinson Hyperlegible
  textScale: number; // root font-size percentage, 90–140
}

export const DEFAULT_PREFS: PrefsState = {
  density: "cozy",
  dyslexia: false,
  textScale: 100,
};

export const PREFS_KEY = "nexus_prefs";
export const TEXT_SCALE_MIN = 90;
export const TEXT_SCALE_MAX = 140;

export function clampScale(n: number): number {
  if (Number.isNaN(n)) return 100;
  return Math.min(TEXT_SCALE_MAX, Math.max(TEXT_SCALE_MIN, Math.round(n)));
}

export function loadPrefs(): PrefsState {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (raw) {
      const p = { ...DEFAULT_PREFS, ...JSON.parse(raw) };
      return { ...p, textScale: clampScale(p.textScale) };
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_PREFS;
}

/** Apply preferences to the document root (data-attributes + root font scale). */
export function applyPrefs(state: PrefsState, root: HTMLElement): void {
  root.dataset.density = state.density;
  root.dataset.dyslexia = state.dyslexia ? "on" : "off";
  root.style.fontSize = state.textScale === 100 ? "" : `${clampScale(state.textScale)}%`;
}

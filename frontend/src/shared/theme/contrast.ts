// WCAG contrast utilities — the deterministic accessibility gate (A7) and the engine the theme
// validator (B10) reuses. Pure functions, no DOM.

export type RGB = { r: number; g: number; b: number };

export function hexToRgb(hex: string): RGB {
  const h = hex.replace("#", "").trim();
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  return {
    r: parseInt(full.slice(0, 2), 16),
    g: parseInt(full.slice(2, 4), 16),
    b: parseInt(full.slice(4, 6), 16),
  };
}

function channel(c: number): number {
  const s = c / 255;
  return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
}

/** WCAG relative luminance (0–1). */
export function luminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex);
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/** WCAG contrast ratio (1–21) between two colors. */
export function contrastRatio(a: string, b: string): number {
  const la = luminance(a);
  const lb = luminance(b);
  const [hi, lo] = la >= lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

export const AA_NORMAL = 4.5;
export const AA_LARGE = 3.0; // ≥18.66px bold or ≥24px, and UI components/graphics
export const AAA_NORMAL = 7.0;

export function meetsAA(fg: string, bg: string, large = false): boolean {
  return contrastRatio(fg, bg) >= (large ? AA_LARGE : AA_NORMAL);
}
export function meetsAAA(fg: string, bg: string): boolean {
  return contrastRatio(fg, bg) >= AAA_NORMAL;
}

/** Two status colors are "distinguishable" if their contrast ratio clears a threshold — used to
 *  keep protected run statuses (running/ok/warn/failed/skipped) telling-apart-able. */
export function distinguishable(a: string, b: string, min = 1.4): boolean {
  return contrastRatio(a, b) >= min;
}

/** Check a set of status colors are pairwise distinguishable; returns the failing pairs. */
export function statusDistinguishability(
  colors: Record<string, string>,
  min = 1.4,
): { from: string; to: string; ratio: number }[] {
  const keys = Object.keys(colors);
  const failures: { from: string; to: string; ratio: number }[] = [];
  for (let i = 0; i < keys.length; i++) {
    for (let j = i + 1; j < keys.length; j++) {
      const ratio = contrastRatio(colors[keys[i]], colors[keys[j]]);
      if (ratio < min) failures.push({ from: keys[i], to: keys[j], ratio });
    }
  }
  return failures;
}

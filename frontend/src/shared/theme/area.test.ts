import { describe, expect, it } from "vitest";
import { contrastRatio, AA_NORMAL, hexToRgb } from "./contrast";

// Area accents (mirrors the @layer area block in tokens.css). Each must be legible with its
// contrast text, and must NOT be confusable with the protected status hues.
const lightAreas = {
  dashboard: "#2f72b0", catalog: "#5a4bb0", canvas: "#0e7c84", library: "#2f6f9e",
  console: "#9b4f8c", incidents: "#b0487f", governance: "#6f4ea8", admin: "#4a5568",
};
const darkAreas = {
  dashboard: "#6ba6db", catalog: "#9b8fe0", canvas: "#4bb3bb", library: "#7fb4dc",
  console: "#d68fc6", incidents: "#df8ac0", governance: "#b29be0", admin: "#93a0b5",
};
const STATUS = { ok: "#4c8a5e", warn: "#b07a1e", failed: "#b23a33" };

function hsl(hex: string): { h: number; s: number } {
  const { r, g, b } = hexToRgb(hex);
  const rn = r / 255, gn = g / 255, bn = b / 255;
  const max = Math.max(rn, gn, bn), min = Math.min(rn, gn, bn), d = max - min;
  const l = (max + min) / 2;
  let h = 0;
  if (d !== 0) {
    if (max === rn) h = ((gn - bn) / d) % 6;
    else if (max === gn) h = (bn - rn) / d + 2;
    else h = (rn - gn) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  return { h, s };
}
function hueDist(a: number, b: number): number {
  const d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}

describe("area accents", () => {
  it("light accents carry white text at AA-normal", () => {
    for (const [area, c] of Object.entries(lightAreas))
      expect(contrastRatio("#ffffff", c), area).toBeGreaterThanOrEqual(AA_NORMAL);
  });

  it("dark accents carry dark text at AA-normal", () => {
    for (const [area, c] of Object.entries(darkAreas))
      expect(contrastRatio("#141210", c), area).toBeGreaterThanOrEqual(AA_NORMAL);
  });

  it("no area accent shares a hue with a protected status (≥30° apart, or near-neutral)", () => {
    const statusHues = Object.values(STATUS).map((s) => hsl(s).h);
    for (const [area, c] of Object.entries(lightAreas)) {
      const { h, s } = hsl(c);
      if (s < 0.2) continue; // near-neutral (e.g. admin slate) can't be mistaken for a status
      for (const sh of statusHues) {
        expect(hueDist(h, sh), `${area} hue ${h.toFixed(0)} vs status ${sh.toFixed(0)}`).toBeGreaterThanOrEqual(30);
      }
    }
  });
});

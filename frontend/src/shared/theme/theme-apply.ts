// Applies a theme by injecting its tokens into the `theme` cascade layer (declared in tokens.css)
// and setting <html data-theme>. Themes are data → CSS is generated at runtime. No AI involved.

import type { ThemeDoc } from "./theme-schema";

function block(selector: string, tokens: Record<string, string>): string {
  const body = Object.entries(tokens)
    .map(([k, v]) => `${k}:${v};`)
    .join("");
  return `${selector}{${body}}`;
}

/** Generate the `@layer theme` CSS for one theme (light under [data-theme], dark under the
 *  dark+theme combo so it wins in dark mode). */
export function themeCss(theme: ThemeDoc): string {
  return (
    `@layer theme {` +
    block(`[data-theme="${theme.id}"]`, theme.tokens.light) +
    block(`[data-mode="dark"][data-theme="${theme.id}"]`, theme.tokens.dark) +
    `}`
  );
}

const STYLE_ID = "nexus-theme-vars";

export function applyTheme(theme: ThemeDoc): void {
  if (typeof document === "undefined") return;
  let el = document.getElementById(STYLE_ID) as HTMLStyleElement | null;
  if (!el) {
    el = document.createElement("style");
    el.id = STYLE_ID;
    document.head.appendChild(el);
  }
  el.textContent = themeCss(theme);
  document.documentElement.dataset.theme = theme.id;
}

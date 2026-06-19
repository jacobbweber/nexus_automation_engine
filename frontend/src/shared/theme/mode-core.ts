// Pure mode-engine logic + types (no React) — kept separate so the provider file only exports
// components/hooks (react-refresh friendly) and so the resolver is trivially unit-testable.

import type { Mode } from "./tokens";

export interface Sundown {
  enabled: boolean;
  start: string; // "HH:MM" — dark turns on
  end: string; // "HH:MM" — dark turns off
}

export interface ModeState {
  preference: Mode; // system | light | dark
  sundown: Sundown;
  perArea: Record<string, Mode>; // area -> override
}

export const DEFAULT_MODE: ModeState = {
  preference: "system",
  sundown: { enabled: false, start: "18:00", end: "06:00" },
  perArea: {},
};

export const MODE_KEY = "nexus_mode";

export function loadMode(): ModeState {
  try {
    const raw = localStorage.getItem(MODE_KEY);
    if (raw) return { ...DEFAULT_MODE, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return DEFAULT_MODE;
}

function minutes(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

/** Pure resolver — given state + context, returns the effective light|dark. */
export function resolveMode(
  state: ModeState,
  ctx: { osDark: boolean; now: Date; activeArea?: string },
): "light" | "dark" {
  const override = ctx.activeArea ? state.perArea[ctx.activeArea] : undefined;
  const pref = override ?? state.preference;
  if (pref === "light") return "light";
  if (pref === "dark") return "dark";
  if (state.sundown.enabled) {
    const now = ctx.now.getHours() * 60 + ctx.now.getMinutes();
    const s = minutes(state.sundown.start);
    const e = minutes(state.sundown.end);
    const dark = s <= e ? now >= s && now < e : now >= s || now < e; // overnight wrap
    return dark ? "dark" : "light";
  }
  return ctx.osDark ? "dark" : "light";
}

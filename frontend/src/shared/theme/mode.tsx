// Mode engine provider (A4): applies the resolved light|dark to <html data-mode>, with
// System/Light/Dark + auto-sundown + per-area override + persistence. Pure logic lives in
// mode-core.ts.

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Mode } from "./tokens";
import { type ModeState, type Sundown, loadMode, MODE_KEY, resolveMode } from "./mode-core";

interface ModeContextValue extends ModeState {
  effective: "light" | "dark";
  activeArea?: string;
  setPreference: (p: Mode) => void;
  setSundown: (s: Sundown) => void;
  setAreaOverride: (area: string, mode: Mode | null) => void;
  setActiveArea: (area?: string) => void;
}

const Ctx = createContext<ModeContextValue | null>(null);

export function ModeProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ModeState>(loadMode);
  const [activeArea, setActiveArea] = useState<string | undefined>();
  const [osDark, setOsDark] = useState(
    () => typeof matchMedia !== "undefined" && matchMedia("(prefers-color-scheme: dark)").matches,
  );

  useEffect(() => {
    if (typeof matchMedia === "undefined") return;
    const mq = matchMedia("(prefers-color-scheme: dark)");
    const on = () => setOsDark(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);

  const effective = useMemo(
    () => resolveMode(state, { osDark, now: new Date(), activeArea }),
    [state, osDark, activeArea],
  );

  useEffect(() => {
    const root = document.documentElement;
    // Keep the legacy `.dark` class (set in index.html for anti-FOUC) in sync with the resolved
    // mode — otherwise its `:where(.dark)` rule pins the app to dark even after switching to light.
    const applyMode = () => {
      root.dataset.mode = effective;
      root.classList.toggle("dark", effective === "dark");
    };
    const reduce = matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (!reduce) {
      root.classList.add("mode-anim");
      const t = setTimeout(() => root.classList.remove("mode-anim"), 260);
      applyMode();
      return () => clearTimeout(t);
    }
    applyMode();
  }, [effective]);

  useEffect(() => {
    if (state.preference !== "system" || !state.sundown.enabled) return;
    const id = setInterval(() => setState((s) => ({ ...s })), 60_000);
    return () => clearInterval(id);
  }, [state.preference, state.sundown.enabled]);

  const persist = useCallback((next: ModeState) => {
    setState(next);
    try {
      localStorage.setItem(MODE_KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }, []);

  const value: ModeContextValue = useMemo(
    () => ({
      ...state,
      effective,
      activeArea,
      setPreference: (p) => persist({ ...state, preference: p }),
      setSundown: (s) => persist({ ...state, sundown: s }),
      setAreaOverride: (area, mode) => {
        const perArea = { ...state.perArea };
        if (mode) perArea[area] = mode;
        else delete perArea[area];
        persist({ ...state, perArea });
      },
      setActiveArea,
    }),
    [state, effective, activeArea, persist],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useMode(): ModeContextValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useMode must be used within ModeProvider");
  return v;
}

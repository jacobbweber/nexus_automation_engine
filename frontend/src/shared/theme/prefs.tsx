// Display/accessibility preferences provider (A5): density, dyslexia font, text-scale.
// Pure logic lives in prefs-core.ts.

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Density } from "./tokens";
import { type PrefsState, applyPrefs, clampScale, loadPrefs, PREFS_KEY } from "./prefs-core";

interface PrefsContextValue extends PrefsState {
  setDensity: (d: Density) => void;
  setDyslexia: (on: boolean) => void;
  setTextScale: (n: number) => void;
}

const Ctx = createContext<PrefsContextValue | null>(null);

export function PrefsProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PrefsState>(loadPrefs);

  useEffect(() => {
    applyPrefs(state, document.documentElement);
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(state));
    } catch {
      /* ignore */
    }
  }, [state]);

  const value: PrefsContextValue = useMemo(
    () => ({
      ...state,
      setDensity: (density) => setState((s) => ({ ...s, density })),
      setDyslexia: (dyslexia) => setState((s) => ({ ...s, dyslexia })),
      setTextScale: (n) => setState((s) => ({ ...s, textScale: clampScale(n) })),
    }),
    [state],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function usePrefs(): PrefsContextValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("usePrefs must be used within PrefsProvider");
  return v;
}

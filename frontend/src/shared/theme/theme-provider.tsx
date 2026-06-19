// Active-theme provider (B11/B12): applies the chosen theme, persists the choice, and merges
// server/volume themes (B12) with the bundled built-ins — hot-reloading via the SSE change stream.

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Themes, openThemeStream, type ServerThemeDoc } from "@/shared/api/client";
import { applyTheme } from "./theme-apply";
import { BUILTIN_THEMES, DEFAULT_THEME_ID, type BuiltinTheme } from "./themes/builtins";

const KEY = "nexus_theme_id";

function loadThemeId(): string {
  try {
    return localStorage.getItem(KEY) || DEFAULT_THEME_ID;
  } catch {
    return DEFAULT_THEME_ID;
  }
}

interface ThemeContextValue {
  themeId: string;
  themes: BuiltinTheme[];
  setTheme: (id: string) => void;
}

const Ctx = createContext<ThemeContextValue | null>(null);

function toBuiltin(d: ServerThemeDoc): BuiltinTheme {
  return { ...d, base: d.base === "dark" ? "dark" : "light", blurb: d.blurb ?? "Custom theme" };
}

export function ThemesProvider({ children }: { children: ReactNode }) {
  const [themeId, setThemeId] = useState<string>(loadThemeId);
  const [serverThemes, setServerThemes] = useState<BuiltinTheme[]>([]);

  const themes = useMemo(() => {
    const ids = new Set(serverThemes.map((t) => t.id));
    return [...BUILTIN_THEMES.filter((t) => !ids.has(t.id)), ...serverThemes];
  }, [serverThemes]);

  // Load server/volume themes + hot-reload when the volume changes.
  useEffect(() => {
    const refresh = () =>
      Themes.list()
        .then((r) => setServerThemes(r.themes.map(toBuiltin)))
        .catch(() => undefined);
    refresh();
    let es: EventSource | undefined;
    try {
      es = openThemeStream();
      es.addEventListener("theme:changed", refresh);
    } catch {
      /* SSE unavailable — built-ins still work */
    }
    return () => es?.close();
  }, []);

  useEffect(() => {
    const theme = themes.find((t) => t.id === themeId) ?? themes[0] ?? BUILTIN_THEMES[0];
    applyTheme(theme);
    try {
      localStorage.setItem(KEY, themeId);
    } catch {
      /* ignore */
    }
  }, [themeId, themes]);

  const value = useMemo<ThemeContextValue>(
    () => ({ themeId, themes, setTheme: setThemeId }),
    [themeId, themes],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTheme(): ThemeContextValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useTheme must be used within ThemesProvider");
  return v;
}

// Active-theme provider (B11): applies the chosen built-in theme + persists the choice.

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { applyTheme } from "./theme-apply";
import { BUILTIN_THEMES, DEFAULT_THEME_ID, type BuiltinTheme } from "./themes/builtins";

const KEY = "nexus_theme_id";

function loadThemeId(): string {
  try {
    const id = localStorage.getItem(KEY);
    if (id && BUILTIN_THEMES.some((t) => t.id === id)) return id;
  } catch {
    /* ignore */
  }
  return DEFAULT_THEME_ID;
}

interface ThemeContextValue {
  themeId: string;
  themes: BuiltinTheme[];
  setTheme: (id: string) => void;
}

const Ctx = createContext<ThemeContextValue | null>(null);

export function ThemesProvider({ children }: { children: ReactNode }) {
  const [themeId, setThemeId] = useState<string>(loadThemeId);

  useEffect(() => {
    const theme = BUILTIN_THEMES.find((t) => t.id === themeId) ?? BUILTIN_THEMES[0];
    applyTheme(theme);
    try {
      localStorage.setItem(KEY, themeId);
    } catch {
      /* ignore */
    }
  }, [themeId]);

  const value = useMemo<ThemeContextValue>(
    () => ({ themeId, themes: BUILTIN_THEMES, setTheme: setThemeId }),
    [themeId],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTheme(): ThemeContextValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useTheme must be used within ThemesProvider");
  return v;
}

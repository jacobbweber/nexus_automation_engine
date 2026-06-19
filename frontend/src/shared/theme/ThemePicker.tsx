// Theme picker — lists the built-in themes with a swatch + blurb. Reused by the shell disclosure
// and (later) the full Theme Studio / Accessibility center.

import { Check } from "lucide-react";
import { useTheme } from "./theme-provider";

export function ThemePicker() {
  const { themeId, themes, setTheme } = useTheme();
  return (
    <div role="radiogroup" aria-label="Theme" style={{ display: "grid", gap: 4 }}>
      {themes.map((t) => {
        const active = t.id === themeId;
        const sw = t.tokens.light;
        return (
          <button
            key={t.id}
            role="radio"
            aria-checked={active}
            title={t.blurb}
            onClick={() => setTheme(t.id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 8px",
              borderRadius: "var(--radius-sm)",
              border: `1px solid ${active ? "var(--area-accent, var(--accent))" : "var(--border)"}`,
              background: active ? "var(--accent-soft)" : "transparent",
              color: "var(--text)",
              cursor: "pointer",
              textAlign: "left",
            }}
          >
            <span
              aria-hidden
              style={{
                display: "inline-flex",
                borderRadius: 999,
                overflow: "hidden",
                border: "1px solid var(--border)",
                flex: "0 0 auto",
              }}
            >
              {[sw["--bg"], sw["--surface-2"], sw["--accent"]].map((c, i) => (
                <span key={i} style={{ width: 10, height: 16, background: c }} />
              ))}
            </span>
            <span style={{ flex: 1, fontSize: "0.78rem", fontWeight: active ? 600 : 500 }}>{t.name}</span>
            {active && <Check size={14} style={{ color: "var(--accent)" }} />}
          </button>
        );
      })}
    </div>
  );
}

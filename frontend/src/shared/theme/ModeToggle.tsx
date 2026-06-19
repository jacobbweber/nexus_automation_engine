// Segmented System / Light / Dark control. Keyboard-accessible (radio-group semantics).

import { Monitor, Moon, Sun } from "lucide-react";
import type { Mode } from "./tokens";
import { useMode } from "./mode";

const OPTIONS: { value: Mode; label: string; icon: typeof Sun }[] = [
  { value: "system", label: "System", icon: Monitor },
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
];

export function ModeToggle() {
  const { preference, setPreference } = useMode();
  return (
    <div
      role="radiogroup"
      aria-label="Color mode"
      style={{
        display: "flex",
        gap: 2,
        padding: 2,
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border)",
        background: "var(--bg)",
      }}
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const active = preference === value;
        return (
          <button
            key={value}
            role="radio"
            aria-checked={active}
            title={label}
            onClick={() => setPreference(value)}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
              flex: 1,
              padding: "6px 8px",
              borderRadius: "calc(var(--radius-md) - 3px)",
              border: "none",
              cursor: "pointer",
              fontSize: "0.74rem",
              background: active ? "var(--area-accent, var(--accent))" : "transparent",
              color: active ? "var(--area-accent-contrast, var(--accent-contrast))" : "var(--text-muted)",
            }}
          >
            <Icon size={14} />
            {label}
          </button>
        );
      })}
    </div>
  );
}

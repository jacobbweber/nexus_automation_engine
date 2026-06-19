// Compact display/accessibility controls — density, dyslexia font, text-scale. Reused by the
// app shell (disclosure) and, later, the full Accessibility center (K44).

import type { Density } from "./tokens";
import { usePrefs } from "./prefs";
import { TEXT_SCALE_MAX, TEXT_SCALE_MIN } from "./prefs-core";

const DENSITIES: Density[] = ["cozy", "comfortable", "compact"];

export function DisplayControls() {
  const { density, setDensity, dyslexia, setDyslexia, textScale, setTextScale } = usePrefs();
  return (
    <div style={{ display: "grid", gap: 10, padding: "6px 4px" }}>
      <Field label="Density">
        <div role="radiogroup" aria-label="Density" style={{ display: "flex", gap: 2 }}>
          {DENSITIES.map((d) => (
            <button
              key={d}
              role="radio"
              aria-checked={density === d}
              onClick={() => setDensity(d)}
              style={{
                flex: 1,
                padding: "5px 6px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border)",
                cursor: "pointer",
                textTransform: "capitalize",
                fontSize: "0.7rem",
                background: density === d ? "var(--area-accent, var(--accent))" : "transparent",
                color: density === d ? "var(--area-accent-contrast, var(--accent-contrast))" : "var(--text-muted)",
              }}
            >
              {d}
            </button>
          ))}
        </div>
      </Field>

      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.74rem", color: "var(--text)" }}>
        <input type="checkbox" checked={dyslexia} onChange={(e) => setDyslexia(e.target.checked)} />
        Dyslexia-friendly font
      </label>

      <Field label={`Text size — ${textScale}%`}>
        <input
          type="range"
          min={TEXT_SCALE_MIN}
          max={TEXT_SCALE_MAX}
          step={5}
          value={textScale}
          onChange={(e) => setTextScale(Number(e.target.value))}
          aria-label="Text size"
          style={{ width: "100%" }}
        />
      </Field>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "grid", gap: 4 }}>
      <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>{label}</span>
      {children}
    </div>
  );
}

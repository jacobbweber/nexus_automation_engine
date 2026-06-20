// Accessibility Center (K44): one place for mode + auto-sundown + per-area overrides, density,
// dyslexia font, text-scale, and theme. Reuses the shared controls; adds the sundown + per-area
// mode UI the engine already supports.

import type { Mode } from "@/shared/theme/tokens";
import { useMode } from "@/shared/theme/mode";
import { DisplayControls } from "@/shared/theme/DisplayControls";
import { ModeToggle } from "@/shared/theme/ModeToggle";
import { ThemePicker } from "@/shared/theme/ThemePicker";
import { Card, Page } from "@/shared/ui/primitives";

const AREAS = ["dashboard", "catalog", "canvas", "library", "console", "incidents", "governance", "admin"];
const MODES: (Mode | "")[] = ["", "system", "light", "dark"];

export function AccessibilityPage() {
  const { preference, sundown, perArea, effective, setSundown, setAreaOverride } = useMode();

  return (
    <Page title="Accessibility Center" subtitle="Make Nexus comfortable to use — applies instantly, saved on this device">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, alignItems: "start" }}>
        <Card>
          <Title>Color mode</Title>
          <ModeToggle />
          <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", margin: "8px 0 0" }}>
            Currently showing <strong>{effective}</strong>{preference === "system" ? " (following your device / sundown)" : ""}.
          </p>

          <div style={{ marginTop: 14 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.82rem" }}>
              <input
                type="checkbox"
                checked={sundown.enabled}
                onChange={(e) => setSundown({ ...sundown, enabled: e.target.checked })}
              />
              Auto-sundown (dark on a schedule in System mode)
            </label>
            {sundown.enabled && (
              <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
                <TimeField label="Dark from" value={sundown.start} onChange={(v) => setSundown({ ...sundown, start: v })} />
                <TimeField label="Light from" value={sundown.end} onChange={(v) => setSundown({ ...sundown, end: v })} />
              </div>
            )}
          </div>

          <div style={{ marginTop: 16 }}>
            <Title>Per-area overrides</Title>
            <p style={{ fontSize: "0.74rem", color: "var(--text-muted)", margin: "0 0 8px" }}>
              Force a mode for a specific surface (e.g. keep the Console dark).
            </p>
            {AREAS.map((area) => (
              <div key={area} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 0" }}>
                <span style={{ fontSize: "0.82rem", textTransform: "capitalize" }}>{area}</span>
                <select
                  value={perArea[area] ?? ""}
                  onChange={(e) => setAreaOverride(area, (e.target.value || null) as Mode | null)}
                  aria-label={`${area} mode override`}
                  style={ctl}
                >
                  {MODES.map((m) => (
                    <option key={m} value={m}>{m === "" ? "Follow global" : m}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </Card>

        <div style={{ display: "grid", gap: 14 }}>
          <Card>
            <Title>Display & reading</Title>
            <DisplayControls />
          </Card>
          <Card>
            <Title>Theme</Title>
            <ThemePicker />
          </Card>
        </div>
      </div>
    </Page>
  );
}

function Title({ children }: { children: React.ReactNode }) {
  return <h2 style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>{children}</h2>;
}
function TimeField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label style={{ display: "grid", gap: 3, fontSize: "0.72rem", color: "var(--text-muted)" }}>
      {label}
      <input type="time" value={value} onChange={(e) => onChange(e.target.value)} style={ctl} />
    </label>
  );
}

const ctl: React.CSSProperties = {
  padding: "6px 9px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)",
  background: "var(--bg)", color: "var(--text)", fontSize: "0.8rem",
};

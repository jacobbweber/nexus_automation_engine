// Side-by-side comparison of 2–3 catalog automations (E23). Pure presentational — fields come
// from the already-loaded Template list, so no extra fetch.

import { X } from "lucide-react";
import type { Template } from "@/shared/api/client";

const ROWS: { label: string; get: (t: Template) => string }[] = [
  { label: "Vendor", get: (t) => t.vendor || t.connector },
  { label: "Domain", get: (t) => t.domain },
  { label: "Risk", get: (t) => t.risk },
  { label: "Type", get: (t) => (t.atomic ? "Atomic" : "Orchestrated") },
  { label: "Est. duration", get: (t) => `~${t.estimated_minutes}m` },
  { label: "Version", get: (t) => t.version },
  { label: "Check mode", get: (t) => (t.supports_check_mode ? "Yes" : "No") },
  { label: "Diff", get: (t) => (t.supports_diff ? "Yes" : "No") },
  { label: "Tags", get: (t) => t.tags.join(", ") || "—" },
  { label: "Prerequisites", get: (t) => t.prerequisites || "—" },
];

export function CompareTemplates({ templates, onClose }: { templates: Template[]; onClose: () => void }) {
  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "var(--overlay)", display: "grid", placeItems: "center", zIndex: 1000, padding: 24 }}
    >
      <div
        role="dialog"
        aria-label="Compare automations"
        onClick={(e) => e.stopPropagation()}
        style={{ width: "min(900px, 96vw)", maxHeight: "86vh", overflow: "auto", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-2xl)", boxShadow: "var(--shadow-3)" }}
      >
        <div style={{ display: "flex", alignItems: "center", padding: "16px 18px", borderBottom: "1px solid var(--border)" }}>
          <h2 style={{ margin: 0, fontSize: "1rem" }}>Compare automations</h2>
          <button onClick={onClose} aria-label="Close" style={{ marginLeft: "auto", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex" }}>
            <X size={18} />
          </button>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.84rem" }}>
          <thead>
            <tr>
              <th style={{ ...cell, width: 150, color: "var(--text-muted)", fontWeight: 600 }}></th>
              {templates.map((t) => (
                <th key={t.id} style={{ ...cell, textAlign: "left" }}>{t.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.label} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ ...cell, color: "var(--text-muted)" }}>{row.label}</td>
                {templates.map((t) => (
                  <td key={t.id} style={cell}>{row.get(t)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const cell: React.CSSProperties = { padding: "10px 14px", textAlign: "left", verticalAlign: "top" };

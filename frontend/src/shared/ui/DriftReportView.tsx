// Drift report viewer — desired-vs-observed per field with the reconcile action. Reused by the
// compliance dashboard, catalog detail "Check compliance", and the canvas.

import type { DriftReport } from "@/shared/api/client";

const STATE_COLOR: Record<string, string> = {
  compliant: "var(--success)",
  drifted: "var(--warn)",
  unknown: "var(--text-muted)",
};

export function ComplianceBadge({ status, count }: { status: string; count?: number }) {
  const color = STATE_COLOR[status] ?? "var(--text-muted)";
  return (
    <span
      style={{
        display: "inline-flex",
        gap: 5,
        alignItems: "center",
        padding: "2px 9px",
        borderRadius: 999,
        fontSize: "0.72rem",
        fontWeight: 600,
        color,
        border: `1px solid ${color}`,
        background: `color-mix(in srgb, ${color} 12%, transparent)`,
      }}
    >
      {status}
      {count != null && count > 0 && <span style={{ opacity: 0.85 }}>· {count} drifted</span>}
    </span>
  );
}

export function DriftReportView({ report }: { report: DriftReport }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <strong style={{ fontSize: "0.9rem" }}>{report.target}</strong>
        <ComplianceBadge status={report.status} count={report.drift_count} />
      </div>
      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 10 }}>
        {report.summary}
      </div>
      {report.resources.map((res, i) => (
        <div
          key={i}
          style={{
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: 10,
            marginBottom: 8,
          }}
        >
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontWeight: 600, fontSize: "0.82rem" }}>{res.resource}</span>
            <ComplianceBadge status={res.state} />
          </div>
          {res.fields.length > 0 && (
            <table style={{ width: "100%", marginTop: 8, fontSize: "0.78rem", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--text-muted)" }}>
                  <th style={th}>Field</th>
                  <th style={th}>Desired</th>
                  <th style={th}>Observed</th>
                </tr>
              </thead>
              <tbody>
                {res.fields.map((f) => (
                  <tr key={f.field}>
                    <td style={td}>{f.field}</td>
                    <td style={{ ...td, color: "var(--success)" }}>{f.desired}</td>
                    <td style={{ ...td, color: "var(--warn)" }}>{f.observed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {res.reconcile_action && (
            <div style={{ marginTop: 6, fontSize: "0.76rem", color: "var(--text-muted)" }}>
              <strong>Reconcile:</strong> {res.reconcile_action}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

const th: React.CSSProperties = { padding: "2px 8px", fontWeight: 600 };
const td: React.CSSProperties = { padding: "2px 8px", borderTop: "1px solid var(--border)" };

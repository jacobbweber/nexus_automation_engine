// CMDB Lineage Explorer (M24.7) — look up a CI's deterministic health report: its score, the
// required relationships (lineage) with gaps highlighted, and field/tag/lineage issues + remediation.

import { useState } from "react";
import { ApiError, Cmdb, type CIHealthReport, type LineageSpec } from "@/shared/api/client";
import { Button } from "@/shared/ui/primitives";
import { HealthBadge } from "@/shared/ui/HealthBadge";

const SAMPLES = ["web-prod-01", "app-stg-01", "ds-vvol-01", "legacy-app-02"];

export function CmdbExplorerPage() {
  const [name, setName] = useState("web-prod-01");
  const [report, setReport] = useState<CIHealthReport | null>(null);
  const [lineage, setLineage] = useState<LineageSpec | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function look(target?: string) {
    const ci = (target ?? name).trim();
    if (!ci) return;
    setBusy(true);
    setError(null);
    setReport(null);
    setLineage(null);
    try {
      const rep = await Cmdb.ciHealth(ci);
      setReport(rep);
      setLineage(await Cmdb.lineageFor(rep.ci_type).catch(() => null));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Lookup failed.");
    } finally {
      setBusy(false);
    }
  }

  // which lineage relationship names have an issue (missing/orphaned/cardinality)
  const brokenRels = new Set((report?.lineage_issues ?? []).map((i) => i.target));

  return (
    <div style={{ maxWidth: 900 }}>
      <h1 style={{ fontSize: "1.2rem", marginBottom: 2 }}>CMDB Lineage Explorer</h1>
      <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: 0 }}>
        Check a configuration item against its schema + lineage — health, gaps, and how to fix them.
      </p>

      <div style={{ display: "flex", gap: 8, alignItems: "center", margin: "12px 0" }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && look()}
          placeholder="CI name (e.g. web-prod-01)"
          style={{
            flex: 1,
            padding: "8px 10px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "var(--text)",
          }}
        />
        <Button onClick={() => look()} disabled={busy}>
          {busy ? "Checking…" : "Check"}
        </Button>
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
        {SAMPLES.map((s) => (
          <button
            key={s}
            onClick={() => {
              setName(s);
              look(s);
            }}
            style={{
              fontSize: "0.72rem",
              padding: "2px 8px",
              borderRadius: 999,
              border: "1px solid var(--border)",
              background: "var(--surface-2)",
              color: "var(--text-muted)",
              cursor: "pointer",
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {error && (
        <div role="alert" style={banner("var(--danger)")}>
          {error}
        </div>
      )}

      {report && (
        <>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: 14,
              borderRadius: 10,
              border: "1px solid var(--border)",
              background: "var(--surface)",
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>{report.ci_id}</div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                type: {report.ci_type}
              </div>
            </div>
            <HealthBadge status={report.status} score={report.score} />
          </div>

          {lineage && lineage.relationships.length > 0 && (
            <Section title="Lineage (required relationships)">
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {lineage.relationships.map((r) => {
                  const broken = brokenRels.has(r.name);
                  const color = broken ? "var(--danger)" : "var(--success)";
                  return (
                    <div
                      key={r.name}
                      style={{
                        padding: "8px 12px",
                        borderRadius: 8,
                        border: `1px solid ${color}`,
                        background: `color-mix(in srgb, ${color} 8%, transparent)`,
                        minWidth: 140,
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: "0.82rem" }}>{r.name}</div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                        → {r.target_type} · {r.cardinality} · {r.required ? "required" : "optional"}
                      </div>
                      <div style={{ fontSize: "0.7rem", color, marginTop: 2 }}>
                        {broken ? "✗ gap" : "✓ satisfied"}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Section>
          )}

          <IssueList title="Field issues" issues={report.field_issues} />
          <IssueList title="Lineage issues" issues={report.lineage_issues} />
          <IssueList title="Tag issues" issues={report.tag_issues} />

          {report.remediation_hints.length > 0 && (
            <Section title="How to fix">
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: "0.84rem" }}>
                {report.remediation_hints.map((h, i) => (
                  <li key={i} style={{ marginBottom: 3 }}>
                    {h}
                  </li>
                ))}
              </ul>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function IssueList({
  title,
  issues,
}: {
  title: string;
  issues: { code: string; target: string; message: string; severity: string }[];
}) {
  if (!issues.length) return null;
  return (
    <Section title={`${title} (${issues.length})`}>
      <ul style={{ margin: 0, paddingLeft: 18, fontSize: "0.82rem" }}>
        {issues.map((i, idx) => (
          <li
            key={idx}
            style={{
              marginBottom: 3,
              color: i.severity === "warning" ? "var(--warn)" : "var(--danger)",
            }}
          >
            {i.message}
          </li>
        ))}
      </ul>
    </Section>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginTop: 16 }}>
      <h2 style={{ fontSize: "0.9rem", margin: "0 0 8px" }}>{title}</h2>
      {children}
    </section>
  );
}

function banner(color: string): React.CSSProperties {
  return {
    padding: "8px 12px",
    borderRadius: 8,
    marginBottom: 12,
    fontSize: "0.82rem",
    color,
    border: `1px solid ${color}`,
    background: `color-mix(in srgb, ${color} 12%, transparent)`,
  };
}

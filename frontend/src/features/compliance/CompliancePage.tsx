// Compliance posture dashboard (M25.5) — estate-wide drift posture from scheduled sweeps:
// % compliant, drift trend, top-drifted, and an admin "Run sweep now". Drift detail uses the
// shared DriftReportView.

import { useCallback, useEffect, useState } from "react";
import { ApiError, Compliance, type PostureSnapshot } from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Button, Card, Page } from "@/shared/ui/primitives";

export function CompliancePage() {
  const { user } = useAuth();
  const [latest, setLatest] = useState<PostureSnapshot | null>(null);
  const [history, setHistory] = useState<PostureSnapshot[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    Compliance.posture().then(setLatest).catch(() => setLatest(null));
    Compliance.history().then(setHistory).catch(() => setHistory([]));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function sweep() {
    setBusy(true);
    setError(null);
    try {
      await Compliance.sweep();
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Sweep failed.");
    } finally {
      setBusy(false);
    }
  }

  const pct = latest?.compliant_pct ?? (latest && latest.evaluated
    ? Math.round((100 * latest.compliant) / latest.evaluated)
    : 100);

  return (
    <Page title="Compliance posture" subtitle="Continuous drift assessment of the estate">
      {error && (
        <div role="alert" style={{ color: "var(--danger)", marginBottom: 10, fontSize: "0.85rem" }}>
          {error}
        </div>
      )}

      {!latest ? (
        <Card>
          <p style={{ color: "var(--text-muted)" }}>
            No compliance sweep yet. Sweeps run on the scheduler cadence; or run one now.
          </p>
          {user?.global_role === "admin" && (
            <Button onClick={sweep} disabled={busy}>
              {busy ? "Sweeping…" : "Run sweep now"}
            </Button>
          )}
        </Card>
      ) : (
        <>
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 14 }}>
            <Stat label="Compliant" value={`${pct}%`} accent="var(--success)" />
            <Stat label="Evaluated" value={String(latest.evaluated)} />
            <Stat label="Drifted" value={String(latest.drifted)} accent="var(--warn)" />
            <Stat label="Drifted fields" value={String(latest.drift_count)} accent="var(--warn)" />
          </div>

          {user?.global_role === "admin" && (
            <div style={{ marginBottom: 14 }}>
              <Button onClick={sweep} disabled={busy}>
                {busy ? "Sweeping…" : "Run sweep now"}
              </Button>
            </div>
          )}

          <Card style={{ marginBottom: 14 }}>
            <SectionTitle>Top drifted</SectionTitle>
            {latest.top_drifted.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                Everything evaluated is in compliance. ✓
              </p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: "0.85rem" }}>
                {latest.top_drifted.map((d) => (
                  <li key={d.target} style={{ marginBottom: 3 }}>
                    {d.target} —{" "}
                    <span style={{ color: "var(--warn)" }}>{d.drift_count} drifted field(s)</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <SectionTitle>Drift trend</SectionTitle>
            <div style={{ display: "flex", gap: 4, alignItems: "flex-end", height: 80 }}>
              {[...history].reverse().map((s) => {
                const p = s.compliant_pct ?? (s.evaluated ? (100 * s.compliant) / s.evaluated : 100);
                return (
                  <div
                    key={s.id}
                    title={`${new Date(s.created_at).toLocaleString()} — ${Math.round(p)}% compliant`}
                    style={{
                      width: 14,
                      height: `${Math.max(4, p)}%`,
                      background: p >= 90 ? "var(--success)" : p >= 60 ? "var(--warn)" : "var(--danger)",
                      borderRadius: 3,
                    }}
                  />
                );
              })}
              {history.length === 0 && (
                <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>No history yet.</span>
              )}
            </div>
          </Card>
        </>
      )}
    </Page>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <Card style={{ minWidth: 130 }}>
      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{label}</div>
      <div style={{ fontSize: "1.6rem", fontWeight: 700, color: accent ?? "var(--text)" }}>{value}</div>
    </Card>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>
      {children}
    </h2>
  );
}

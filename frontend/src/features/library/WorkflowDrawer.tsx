// Per-workflow drill-down drawer (G32): usage summary + recent run history, with quick links to
// the canvas. Uses the existing /canvas/workflows/{id}/runs endpoint.

import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Canvas, type WorkflowReport, type WorkflowRun } from "@/shared/api/client";
import { Button, StatusBadge } from "@/shared/ui/primitives";
import { EmptyState } from "@/shared/ui/EmptyState";

function durationLabel(r: WorkflowRun): string {
  if (!r.completed_at) return "—";
  const ms = Date.parse(r.completed_at) - Date.parse(r.started_at);
  if (!Number.isFinite(ms) || ms < 0) return "—";
  const s = Math.round(ms / 1000);
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

export function WorkflowDrawer({ report, onClose }: { report: WorkflowReport; onClose: () => void }) {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<WorkflowRun[] | null>(null);

  useEffect(() => {
    Canvas.runs(report.id).then(setRuns).catch(() => setRuns([]));
  }, [report.id]);

  const u = report.usage;
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "var(--overlay)", display: "flex", justifyContent: "flex-end", zIndex: 1000 }}>
      <div
        role="dialog"
        aria-label={`${report.name} details`}
        onClick={(e) => e.stopPropagation()}
        style={{ width: "min(460px, 96vw)", height: "100%", overflow: "auto", background: "var(--surface)", borderLeft: "1px solid var(--border)", boxShadow: "var(--shadow-3)" }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "16px 18px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700 }}>{report.name}</div>
            <div style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>
              {report.team || "—"} · {report.owner || "—"} · <StatusBadge status={report.review_state} />
            </div>
          </div>
          <button onClick={onClose} aria-label="Close" style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex" }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, padding: 16 }}>
          <Metric label="Runs" value={String(u.run_count)} />
          <Metric label="Success" value={u.run_count ? `${Math.round(u.success_rate * 100)}%` : "—"} />
          <Metric label="Failed" value={String(u.failure_count)} />
        </div>

        <div style={{ padding: "0 16px 16px" }}>
          <div style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 6 }}>
            Recent runs
          </div>
          {runs === null && <div style={{ color: "var(--text-muted)", fontSize: "0.84rem" }}>Loading…</div>}
          {runs !== null && runs.length === 0 && <EmptyState title="No runs yet" description="This workflow hasn't been executed." />}
          {runs && runs.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
              <tbody>
                {runs.slice(0, 25).map((r) => (
                  <tr key={r.run_id} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "7px 4px" }}><StatusBadge status={r.status} /></td>
                    <td style={{ padding: "7px 4px", color: "var(--text-muted)", fontSize: "0.76rem" }}>
                      {r.started_at ? new Date(r.started_at).toLocaleString() : ""}
                    </td>
                    <td style={{ padding: "7px 4px", textAlign: "right", color: "var(--text-muted)" }}>{durationLabel(r)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ padding: "0 16px 18px", display: "flex", gap: 8 }}>
          <Button size="sm" onClick={() => navigate(`/canvas?id=${report.id}`)}>Open in canvas</Button>
          <Button size="sm" variant="ghost" onClick={() => navigate("/console")}>View runs in console</Button>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "10px 12px" }}>
      <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>{label}</div>
      <div style={{ fontSize: "1.2rem", fontWeight: 700 }}>{value}</div>
    </div>
  );
}

// Per-workflow drill-down drawer (G32): usage summary + recent run history, with quick links to
// the canvas. Uses the existing /canvas/workflows/{id}/runs endpoint.

import { ChevronDown, ChevronRight, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Canvas, type WorkflowReport, type WorkflowRun, type WorkflowStep } from "@/shared/api/client";
import { Button, StatusBadge } from "@/shared/ui/primitives";
import { EmptyState } from "@/shared/ui/EmptyState";

function durationLabel(r: WorkflowRun): string {
  if (!r.completed_at) return "—";
  const ms = Date.parse(r.completed_at) - Date.parse(r.started_at);
  if (!Number.isFinite(ms) || ms < 0) return "—";
  const s = Math.round(ms / 1000);
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

export function WorkflowDrawer({
  report,
  onClose,
  onChanged,
}: {
  report: WorkflowReport;
  onClose: () => void;
  onChanged?: () => void;
}) {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<WorkflowRun[] | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Canvas.runs(report.id).then(setRuns).catch(() => setRuns([]));
  }, [report.id]);

  async function submitForReview() {
    setBusy(true);
    try {
      await Canvas.submitForReview(report.id);
      onChanged?.();
      onClose();
    } catch {
      setBusy(false);
    }
  }

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
            <div>
              {runs.slice(0, 25).map((r) => (
                <RunRow key={r.run_id} run={r} onReplay={() => navigate(`/canvas?id=${report.id}&replay=${r.run_id}`)} />
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: "0 16px 18px", display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button size="sm" onClick={() => navigate(`/canvas?id=${report.id}`)}>Open in canvas</Button>
          <Button size="sm" variant="ghost" onClick={() => navigate("/console")}>View runs in console</Button>
          {report.review_state === "draft" && (
            <Button size="sm" variant="soft" onClick={submitForReview} disabled={busy}>
              {busy ? "Submitting…" : "Submit for review"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function spanLabel(start: string, end: string | null): string {
  if (!end) return "—";
  const ms = Date.parse(end) - Date.parse(start);
  if (!Number.isFinite(ms) || ms < 0) return "—";
  const s = Math.round(ms / 1000);
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

// A run row that expands to its per-step timeline (fetched on demand from /canvas/runs/{id}).
function RunRow({ run, onReplay }: { run: WorkflowRun; onReplay: () => void }) {
  const [open, setOpen] = useState(false);
  const [steps, setSteps] = useState<WorkflowStep[] | null>(null);

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next && steps === null) {
      Canvas.getRun(run.run_id).then((r) => setSteps(r.steps ?? [])).catch(() => setSteps([]));
    }
  }

  return (
    <div style={{ borderTop: "1px solid var(--border)" }}>
      <button
        onClick={toggle}
        aria-expanded={open}
        style={{ display: "flex", alignItems: "center", gap: 8, width: "100%", textAlign: "left", background: "none", border: "none", color: "var(--text)", cursor: "pointer", padding: "7px 4px" }}
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <StatusBadge status={run.status} />
        <span style={{ color: "var(--text-muted)", fontSize: "0.76rem" }}>
          {run.started_at ? new Date(run.started_at).toLocaleString() : ""}
        </span>
        <span style={{ marginLeft: "auto", color: "var(--text-muted)", fontSize: "0.76rem" }}>{durationLabel(run)}</span>
        <span
          role="button"
          tabIndex={0}
          onClick={(e) => { e.stopPropagation(); onReplay(); }}
          onKeyDown={(e) => { if (e.key === "Enter") { e.stopPropagation(); onReplay(); } }}
          title="Replay this run on the canvas"
          style={{ color: "var(--accent)", fontSize: "0.72rem", cursor: "pointer" }}
        >
          ▶ replay
        </span>
      </button>
      {open && (
        <div style={{ padding: "2px 4px 10px 26px" }}>
          {steps === null && <div style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>Loading steps…</div>}
          {steps && steps.length === 0 && <div style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>No step detail recorded.</div>}
          {steps?.map((st) => (
            <div key={st.step_id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "3px 0", fontSize: "0.78rem" }}>
              <StatusBadge status={st.status} />
              <span>{st.node_id}</span>
              <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>{st.node_type}{st.retry_count ? ` · ${st.retry_count} retries` : ""}</span>
              <span style={{ marginLeft: "auto", color: "var(--text-muted)", fontSize: "0.72rem" }}>{spanLabel(st.started_at, st.completed_at)}</span>
            </div>
          ))}
        </div>
      )}
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

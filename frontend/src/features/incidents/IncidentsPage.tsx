import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Incidents, type Incident } from "@/shared/api/client";
import { Button, Page } from "@/shared/ui/primitives";

const COLUMNS: { key: string; label: string }[] = [
  { key: "new", label: "New" },
  { key: "triage", label: "Triage" },
  { key: "investigating", label: "Investigating" },
  { key: "resolved", label: "Resolved" },
];
const NEXT: Record<string, string | null> = {
  new: "triage",
  triage: "investigating",
  investigating: "resolved",
  resolved: null,
};
const SEV_COLOR: Record<string, string> = {
  low: "var(--color-ok)",
  medium: "var(--color-warn)",
  high: "var(--color-danger)",
  critical: "#b5402f",
};

export function IncidentsPage() {
  const [board, setBoard] = useState<Record<string, Incident[]>>({});
  const navigate = useNavigate();

  const refresh = useCallback(() => {
    Incidents.board().then(setBoard).catch(() => setBoard({}));
  }, []);
  useEffect(refresh, [refresh]);

  function move(inc: Incident) {
    const next = NEXT[inc.status];
    if (next) Incidents.move(inc.id, next).then(refresh);
  }
  function remediate(inc: Incident) {
    Incidents.remediate(inc.id).then(() => navigate("/canvas"));
  }

  const total = COLUMNS.reduce((n, c) => n + (board[c.key]?.length ?? 0), 0);

  return (
    <Page title="Incidents" subtitle={`${total} captured · failures auto-open here for triage`}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {COLUMNS.map((col) => (
          <div key={col.key} style={{ background: "var(--surface-2)", borderRadius: 10, padding: 10, minHeight: 200 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 8 }}>
              <span>{col.label}</span>
              <span>{board[col.key]?.length ?? 0}</span>
            </div>
            {(board[col.key] ?? []).map((inc) => (
              <div key={inc.id} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: 10, marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.6rem", textTransform: "uppercase", fontWeight: 700, color: SEV_COLOR[inc.severity] ?? "var(--text-muted)" }}>
                    {inc.severity}
                  </span>
                  <span style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>{inc.source_type}</span>
                </div>
                <div style={{ fontSize: "0.82rem", fontWeight: 600, margin: "4px 0" }}>{inc.title}</div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", maxHeight: 48, overflow: "hidden" }}>
                  {inc.summary}
                </div>
                <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
                  {NEXT[inc.status] && (
                    <Button onClick={() => move(inc)}>→ {NEXT[inc.status]}</Button>
                  )}
                  {!inc.remediation_workflow_id && inc.status !== "resolved" && (
                    <Button variant="ghost" onClick={() => remediate(inc)}>Remediate</Button>
                  )}
                  {inc.remediation_workflow_id && (
                    <span style={{ fontSize: "0.68rem", color: "var(--color-accent)", alignSelf: "center" }}>
                      remediation linked
                    </span>
                  )}
                </div>
              </div>
            ))}
            {(board[col.key]?.length ?? 0) === 0 && (
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", padding: 6 }}>—</div>
            )}
          </div>
        ))}
      </div>
    </Page>
  );
}

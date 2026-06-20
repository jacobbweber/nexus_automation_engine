import { PanelRight, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Canvas, type WorkflowReport } from "@/shared/api/client";
import { Card, Page, StatusBadge } from "@/shared/ui/primitives";
import { EmptyState } from "@/shared/ui/EmptyState";
import { useFavorites } from "@/shared/hooks/favorites";
import { WorkflowDrawer } from "./WorkflowDrawer";

// The workflow library + reporting view: who made each workflow, which team owns it, how it's
// used (run counts, last run, success rate), and its governance state — filterable by team/tag,
// with one click to open it in the canvas.
export function WorkflowLibraryPage() {
  const nav = useNavigate();
  const { has: isFav, toggle: toggleFav } = useFavorites();
  const [reports, setReports] = useState<WorkflowReport[]>([]);
  const [drawer, setDrawer] = useState<WorkflowReport | null>(null);
  const [team, setTeam] = useState("");
  const [tag, setTag] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    Canvas.report().then(setReports).catch(() => undefined);
  }, []);

  const teams = useMemo(
    () => [...new Set(reports.map((r) => r.team).filter(Boolean))].sort(),
    [reports],
  );
  const tags = useMemo(
    () => [...new Set(reports.flatMap((r) => r.tags))].sort(),
    [reports],
  );

  const filtered = reports.filter(
    (r) =>
      (!team || r.team === team) &&
      (!tag || r.tags.includes(tag)) &&
      (!search || r.name.toLowerCase().includes(search.toLowerCase())),
  );

  const totalRuns = reports.reduce((a, r) => a + r.usage.run_count, 0);
  const published = reports.filter((r) => r.review_state === "published").length;

  return (
    <Page title="Workflow Library" subtitle="Saved workflows across teams — ownership, usage & governance">
      <Card style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", gap: 28 }}>
          <Stat label="Workflows" value={reports.length} />
          <Stat label="Published" value={published} color="var(--color-ok)" />
          <Stat label="Teams" value={teams.length} />
          <Stat label="Total runs" value={totalRuns} color="var(--color-accent)" />
        </div>
      </Card>

      <Card style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            placeholder="Search workflows…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ ...field, flex: 2 }}
          />
          <select value={team} onChange={(e) => setTeam(e.target.value)} style={field}>
            <option value="">All teams</option>
            {teams.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <select value={tag} onChange={(e) => setTag(e.target.value)} style={field}>
            <option value="">All tags</option>
            {tags.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </Card>

      <Card>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.84rem" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--text-muted)", fontSize: "0.72rem" }}>
              <th style={{ ...th, width: 28 }} aria-label="Favorite"></th>
              <th style={th}>Workflow</th>
              <th style={th}>Team</th>
              <th style={th}>Owner</th>
              <th style={th}>State</th>
              <th style={{ ...th, textAlign: "right" }}>Runs</th>
              <th style={{ ...th, textAlign: "right" }}>Success</th>
              <th style={{ ...th, textAlign: "right" }}>Last run</th>
              <th style={{ ...th, width: 28 }} aria-label="Details"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr
                key={r.id}
                onClick={() => nav(`/canvas?id=${r.id}`)}
                style={{ borderTop: "1px solid var(--border)", cursor: "pointer" }}
                title="Open in canvas"
              >
                <td style={{ ...td, width: 28 }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFav(r.id);
                    }}
                    aria-label={isFav(r.id) ? "Unfavorite" : "Favorite"}
                    aria-pressed={isFav(r.id)}
                    title={isFav(r.id) ? "Unfavorite" : "Favorite"}
                    style={{ background: "none", border: "none", cursor: "pointer", color: isFav(r.id) ? "var(--warn)" : "var(--text-subtle)", display: "flex", padding: 2 }}
                  >
                    <Star size={15} fill={isFav(r.id) ? "currentColor" : "none"} />
                  </button>
                </td>
                <td style={td}>
                  <div>{r.name}</div>
                  <div style={{ display: "flex", gap: 4, marginTop: 3, flexWrap: "wrap" }}>
                    {r.tags.map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                    <span style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>
                      {r.node_count} nodes
                    </span>
                  </div>
                </td>
                <td style={td}>{r.team || "—"}</td>
                <td style={td}>{r.owner || "—"}</td>
                <td style={td}><StatusBadge status={r.review_state} /></td>
                <td style={{ ...td, textAlign: "right" }}>{r.usage.run_count}</td>
                <td style={{ ...td, textAlign: "right" }}>
                  <SuccessRate usage={r.usage} />
                </td>
                <td style={{ ...td, textAlign: "right", color: "var(--text-muted)", fontSize: "0.76rem" }}>
                  {r.usage.last_run_at ? new Date(r.usage.last_run_at).toLocaleDateString() : "never"}
                </td>
                <td style={{ ...td, width: 28 }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDrawer(r);
                    }}
                    aria-label={`Details for ${r.name}`}
                    title="Details & run history"
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-subtle)", display: "flex", padding: 2 }}
                  >
                    <PanelRight size={15} />
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9}>
                  <EmptyState
                    title={reports.length === 0 ? "No workflows yet" : "No workflows match these filters"}
                    description={
                      reports.length === 0
                        ? "Saved workflows will appear here with their team, owner, and usage."
                        : "Try clearing the team or tag filter, or a different search."
                    }
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
      {drawer && <WorkflowDrawer report={drawer} onClose={() => setDrawer(null)} />}
    </Page>
  );
}

function SuccessRate({ usage }: { usage: WorkflowReport["usage"] }) {
  const finished = usage.success_count + usage.failure_count;
  if (finished === 0) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  const pct = Math.round(usage.success_rate * 100);
  const color = pct >= 90 ? "var(--color-ok)" : pct >= 70 ? "var(--color-warn)" : "var(--color-danger)";
  return <span style={{ color }}>{pct}%</span>;
}

function Stat({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: color ?? "var(--text)" }}>{value}</div>
      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{label}</div>
    </div>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        fontSize: "0.66rem",
        padding: "1px 6px",
        borderRadius: 10,
        background: "var(--surface-2)",
        color: "var(--text-muted)",
        border: "1px solid var(--border)",
      }}
    >
      {children}
    </span>
  );
}

const th: React.CSSProperties = { padding: "4px 6px", fontWeight: 600 };
const td: React.CSSProperties = { padding: "9px 6px", verticalAlign: "top" };
const field: React.CSSProperties = {
  flex: 1,
  minWidth: 120,
  padding: "7px 9px",
  borderRadius: 7,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
};

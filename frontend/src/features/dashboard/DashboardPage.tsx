import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Canvas,
  Jobs,
  Schedules,
  Validation,
  type Job,
  type ReviewStatus,
  type Schedule,
  type Workflow,
} from "@/shared/api/client";
import { Card, Page, StatusBadge } from "@/shared/ui/primitives";
import { EmptyState } from "@/shared/ui/EmptyState";
import { useFavorites } from "@/shared/hooks/favorites";
import { formatDuration, summarizeJobs } from "./summary";

export function DashboardPage() {
  const navigate = useNavigate();
  const { ids: favIds } = useFavorites();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [pendingReviews, setPendingReviews] = useState<Workflow[]>([]);
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);

  useEffect(() => {
    Jobs.list().then(setJobs).catch(() => setJobs([]));
    Schedules.list().then(setSchedules).catch(() => setSchedules([]));
    Canvas.pendingReviews().then(setPendingReviews).catch(() => setPendingReviews([]));
    Validation.reviewStatus().then(setReviewStatus).catch(() => setReviewStatus(null));
    Canvas.list().then(setWorkflows).catch(() => setWorkflows([]));
  }, []);

  const favorites = useMemo(
    () => workflows.filter((w) => favIds.includes(w.id)),
    [workflows, favIds],
  );

  const s = useMemo(() => summarizeJobs(jobs), [jobs]);
  const recent = useMemo(
    () => [...jobs].sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? "")).slice(0, 12),
    [jobs],
  );
  const upcoming = useMemo(
    () =>
      [...schedules]
        .filter((x) => x.enabled)
        .sort((a, b) => (a.next_run_at ?? "").localeCompare(b.next_run_at ?? ""))
        .slice(0, 5),
    [schedules],
  );

  return (
    <Page title="Operations Dashboard" subtitle="Fleet pulse across all automation engines">
      {/* fleet pulse — clickable through to the console / incidents */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 14 }}>
        <Stat label="Running" value={s.running} color="var(--run-running)" onClick={() => navigate("/console")} />
        <Stat label="Succeeded" value={s.succeeded} color="var(--run-ok)" onClick={() => navigate("/console")} />
        <Stat label="Failed" value={s.failed} color="var(--run-failed)" onClick={() => navigate("/incidents")} />
        <Stat label="Pending" value={s.pending} color="var(--run-warn)" onClick={() => navigate("/console")} />
      </div>

      {/* trends */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 18 }}>
        <Card>
          <Label>Success rate</Label>
          <Big color={rateColor(s.successRate)}>{s.successRate == null ? "—" : `${Math.round(s.successRate * 100)}%`}</Big>
          <Sub>{s.succeeded + s.failed} finished runs</Sub>
        </Card>
        <Card>
          <Label>Avg run duration</Label>
          <Big>{formatDuration(s.avgDurationMs)}</Big>
          <Sub>across completed runs</Sub>
        </Card>
        <Card>
          <Label>Total runs</Label>
          <Big>{s.total}</Big>
          <Sub>{s.running} in flight</Sub>
        </Card>
      </div>

      {/* needs attention + favorites */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>
        <Card>
          <SectionTitle>Needs attention</SectionTitle>
          {(() => {
            const items: { label: string; count: number; to: string }[] = [
              { label: "Workflows awaiting review", count: pendingReviews.length, to: "/governance" },
              { label: "Failed runs", count: s.failed, to: "/incidents" },
              { label: "Stale automations", count: reviewStatus?.stale ?? 0, to: "/governance" },
              { label: "Never reviewed", count: reviewStatus?.never_reviewed ?? 0, to: "/governance" },
            ].filter((i) => i.count > 0);
            if (items.length === 0)
              return <EmptyState title="All clear" description="No approvals, failures, or stale automations need you right now." />;
            return items.map((i) => (
              <div
                key={i.label}
                onClick={() => navigate(i.to)}
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 0", borderTop: "1px solid var(--border)", cursor: "pointer" }}
              >
                <span style={{ fontSize: "0.85rem" }}>{i.label}</span>
                <span style={{ fontWeight: 700, color: "var(--area-accent)" }}>{i.count}</span>
              </div>
            ));
          })()}
        </Card>

        <Card>
          <SectionTitle>Favorites</SectionTitle>
          {favorites.length === 0 ? (
            <EmptyState title="No favorites yet" description="Star workflows in the Library to pin them here." />
          ) : (
            favorites.map((w) => (
              <div
                key={w.id}
                onClick={() => navigate(`/canvas?id=${w.id}`)}
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 0", borderTop: "1px solid var(--border)", cursor: "pointer" }}
              >
                <span style={{ fontSize: "0.85rem" }}>{w.name}</span>
                <span style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>{w.team}</span>
              </div>
            ))
          )}
        </Card>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 14 }}>
        {/* recent activity */}
        <Card>
          <SectionTitle>Recent activity</SectionTitle>
          {recent.length === 0 ? (
            <EmptyState title="No runs yet" description="Executed automations will stream in here." />
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
              <tbody>
                {recent.map((j) => (
                  <tr
                    key={j.id}
                    onClick={() => navigate("/console")}
                    style={{ borderTop: "1px solid var(--border)", cursor: "pointer" }}
                  >
                    <td style={{ padding: "9px 6px" }}>{j.name}</td>
                    <td style={{ padding: "9px 6px", color: "var(--text-muted)" }}>{j.connector}</td>
                    <td style={{ padding: "9px 6px", color: "var(--text-muted)", fontSize: "0.78rem" }}>
                      {j.created_at ? new Date(j.created_at).toLocaleString() : ""}
                    </td>
                    <td style={{ padding: "9px 6px", textAlign: "right" }}>
                      <StatusBadge status={j.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        {/* change-window / schedule peek */}
        <Card>
          <SectionTitle>Upcoming scheduled</SectionTitle>
          {upcoming.length === 0 ? (
            <EmptyState title="Nothing scheduled" description="Scheduled runs and change windows appear here." />
          ) : (
            upcoming.map((sc) => (
              <div
                key={sc.id}
                onClick={() => navigate("/governance")}
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderTop: "1px solid var(--border)", cursor: "pointer" }}
              >
                <span style={{ fontSize: "0.84rem" }}>{sc.name}</span>
                <span style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>
                  {sc.next_run_at ? new Date(sc.next_run_at).toLocaleString() : ""}
                </span>
              </div>
            ))
          )}
        </Card>
      </div>
    </Page>
  );
}

function rateColor(rate: number | null): string {
  if (rate == null) return "var(--text)";
  const pct = rate * 100;
  return pct >= 90 ? "var(--run-ok)" : pct >= 70 ? "var(--run-warn)" : "var(--run-failed)";
}

function Stat({ label, value, color, onClick }: { label: string; value: number; color?: string; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{ textAlign: "left", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", background: "var(--surface)", boxShadow: "var(--shadow-1)", padding: "var(--space-5)", cursor: onClick ? "pointer" : "default" }}
    >
      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
      <div style={{ fontSize: "1.8rem", fontWeight: 700, color: color ?? "var(--text)" }}>{value}</div>
    </button>
  );
}
function Label({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{children}</div>;
}
function Big({ children, color }: { children: React.ReactNode; color?: string }) {
  return <div style={{ fontSize: "1.8rem", fontWeight: 700, color: color ?? "var(--text)" }}>{children}</div>;
}
function Sub({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{children}</div>;
}
function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>{children}</h2>;
}

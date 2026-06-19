import { useEffect, useState } from "react";
import { Jobs, type Job } from "@/shared/api/client";
import { Card, Page, StatusBadge } from "@/shared/ui/primitives";

export function DashboardPage() {
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    Jobs.list().then(setJobs).catch(() => setJobs([]));
  }, []);

  const counts = jobs.reduce<Record<string, number>>((acc, j) => {
    acc[j.status] = (acc[j.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <Page title="Operations Dashboard" subtitle="Live view across all automation engines">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 18 }}>
        <Stat label="Total runs" value={jobs.length} />
        <Stat label="Succeeded" value={counts.SUCCESS ?? 0} color="var(--color-ok)" />
        <Stat label="Failed" value={counts.FAILED ?? 0} color="var(--color-danger)" />
        <Stat label="Running" value={counts.RUNNING ?? 0} color="var(--color-accent)" />
      </div>
      <Card>
        <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>
          Recent runs
        </h2>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
          <tbody>
            {jobs.slice(0, 12).map((j) => (
              <tr key={j.id} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ padding: "9px 6px" }}>{j.name}</td>
                <td style={{ padding: "9px 6px", color: "var(--text-muted)" }}>{j.connector}</td>
                <td style={{ padding: "9px 6px", color: "var(--text-muted)" }}>{j.initiated_by}</td>
                <td style={{ padding: "9px 6px", textAlign: "right" }}>
                  <StatusBadge status={j.status} />
                </td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr>
                <td style={{ padding: "12px 6px", color: "var(--text-muted)" }}>No runs yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <Card>
      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
      <div style={{ fontSize: "1.8rem", fontWeight: 700, color: color ?? "var(--text)" }}>{value}</div>
    </Card>
  );
}

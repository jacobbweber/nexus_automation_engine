import { ChevronDown, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { Connectors, getHealth, getPlatformStatus, type Capabilities, type PlatformStatus } from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Card, Page } from "@/shared/ui/primitives";

function uptime(s: number): string {
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  return h < 24 ? `${h}h ${m % 60}m` : `${Math.floor(h / 24)}d ${h % 24}h`;
}

export function AdminPage() {
  const { user } = useAuth();
  const [connectors, setConnectors] = useState<Capabilities[]>([]);
  const [simulated, setSimulated] = useState<boolean | null>(null);
  const [status, setStatus] = useState<PlatformStatus | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  useEffect(() => {
    Connectors.list().then(setConnectors).catch(() => setConnectors([]));
    getHealth().then((h) => setSimulated(h.simulation_mode)).catch(() => setSimulated(null));
    getPlatformStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  return (
    <Page title="Administration" subtitle="Connector registry, capabilities, and platform access">
      <Card style={{ marginBottom: 14 }}>
        <SectionTitle>Your access</SectionTitle>
        <div style={{ fontSize: "0.9rem" }}>
          {user?.username} — global role <strong style={{ color: "var(--area-accent)" }}>{user?.global_role}</strong>
        </div>
      </Card>

      {status && (
        <Card style={{ marginBottom: 14 }}>
          <SectionTitle>Platform status</SectionTitle>
          <div style={{ display: "flex", gap: 28, flexWrap: "wrap" }}>
            <Metric label="Status" value={status.db_ok ? "Healthy" : "Degraded"} color={status.db_ok ? "var(--run-ok)" : "var(--run-failed)"} />
            <Metric label="Uptime" value={uptime(status.uptime_seconds)} />
            <Metric label="Workflows" value={String(status.workflows)} />
            <Metric label="Jobs" value={String(status.jobs)} />
            <Metric label="Scheduler" value={status.scheduler_enabled ? "on" : "off"} />
            <Metric label="Environment" value={status.environment} />
            <Metric label="Version" value={status.version} />
          </div>
        </Card>
      )}

      <Card style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <SectionTitle>Connector registry</SectionTitle>
          <span style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 6, fontSize: "0.74rem", color: "var(--text-muted)" }}>
            {simulated !== false ? (
              <>
                <Dot color="var(--run-ok)" /> All connectors simulated (local, nothing leaves this machine)
              </>
            ) : (
              <>
                <Dot color="var(--run-warn)" /> Live connectors configured
              </>
            )}
          </span>
        </div>
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 14 }}>
        {connectors.map((c) => {
          const isOpen = open[c.kind];
          return (
            <Card key={c.kind}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <h3 style={{ margin: "0 0 4px", fontSize: "1rem" }}>{c.display_name}</h3>
                <span style={{ fontSize: "0.66rem", textTransform: "uppercase", color: "var(--text-muted)" }}>{c.category}</span>
              </div>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: "0 0 8px" }}>{c.description}</p>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
                {simulated !== false && <Chip>simulated</Chip>}
                {c.supports_check_mode && <Chip>check-mode</Chip>}
                {c.supports_diff && <Chip>diff</Chip>}
                {c.streams_logs && <Chip>streams logs</Chip>}
              </div>
              <button
                onClick={() => setOpen((o) => ({ ...o, [c.kind]: !o[c.kind] }))}
                aria-expanded={!!isOpen}
                style={{ display: "flex", alignItems: "center", gap: 6, background: "none", border: "none", color: "var(--accent)", cursor: "pointer", fontSize: "0.78rem", padding: 0 }}
              >
                {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                {c.actions.length} action{c.actions.length === 1 ? "" : "s"}
              </button>
              {isOpen && (
                <div style={{ marginTop: 6 }}>
                  {c.actions.map((a) => (
                    <div key={a.name} style={{ padding: "5px 0", borderTop: "1px solid var(--divider)" }}>
                      <div style={{ fontSize: "0.82rem" }}>{a.label}</div>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        {a.name} · {a.params.length} param{a.params.length === 1 ? "" : "s"}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </Page>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>{children}</h2>;
}
function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: "1.3rem", fontWeight: 700, color: color ?? "var(--text)" }}>{value}</div>
      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{label}</div>
    </div>
  );
}
function Dot({ color }: { color: string }) {
  return <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, display: "inline-block" }} />;
}
function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span style={{ fontSize: "0.66rem", padding: "1px 7px", borderRadius: "var(--radius-pill)", background: "var(--surface-2)", color: "var(--text-muted)", border: "1px solid var(--border)" }}>
      {children}
    </span>
  );
}

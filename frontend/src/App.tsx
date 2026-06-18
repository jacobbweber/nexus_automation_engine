import { useEffect, useState } from "react";
import { AppShell } from "@/app/AppShell";
import { getHealth, type Health } from "@/shared/api/client";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <AppShell>
      <div style={{ padding: 32, maxWidth: 880 }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>
          Nexus Automation Engine
        </h1>
        <p style={{ color: "var(--text-muted)", marginTop: 8 }}>
          Unified, vendor-agnostic automation control plane — operator surface coming online
          milestone by milestone.
        </p>

        <section
          style={{
            marginTop: 28,
            padding: 20,
            borderRadius: 12,
            border: "1px solid var(--border)",
            background: "var(--surface)",
          }}
        >
          <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1 }}>
            Backend status
          </h2>
          {health ? (
            <div data-testid="health-ok" style={{ marginTop: 10 }}>
              <StatusDot color="var(--color-ok)" /> {health.app} v{health.version} —{" "}
              {health.environment}
              {health.simulation_mode ? " · simulation" : ""}
            </div>
          ) : error ? (
            <div data-testid="health-error" style={{ marginTop: 10 }}>
              <StatusDot color="var(--color-danger)" /> backend unreachable ({error})
            </div>
          ) : (
            <div style={{ marginTop: 10, color: "var(--text-muted)" }}>checking…</div>
          )}
        </section>
      </div>
    </AppShell>
  );
}

function StatusDot({ color }: { color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 9,
        height: 9,
        borderRadius: "50%",
        background: color,
        marginRight: 8,
      }}
    />
  );
}

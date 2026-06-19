import { useEffect, useState } from "react";
import { Connectors, type Capabilities } from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Card, Page } from "@/shared/ui/primitives";

export function AdminPage() {
  const { user } = useAuth();
  const [connectors, setConnectors] = useState<Capabilities[]>([]);

  useEffect(() => {
    Connectors.list().then(setConnectors).catch(() => setConnectors([]));
  }, []);

  return (
    <Page title="Administration" subtitle="Connectors, capabilities, and platform governance">
      <Card style={{ marginBottom: 14 }}>
        <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>
          Your access
        </h2>
        <div style={{ fontSize: "0.9rem" }}>
          {user?.username} — global role <strong style={{ color: "var(--color-accent)" }}>{user?.global_role}</strong>
        </div>
      </Card>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 14 }}>
        {connectors.map((c) => (
          <Card key={c.kind}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <h3 style={{ margin: "0 0 4px", fontSize: "1rem" }}>{c.display_name}</h3>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{c.category}</span>
            </div>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>{c.description}</p>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {c.supports_check_mode && "check-mode · "}
              {c.supports_diff && "diff · "}
              {c.actions.length} action(s)
            </div>
          </Card>
        ))}
      </div>
    </Page>
  );
}

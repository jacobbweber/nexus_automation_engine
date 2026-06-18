import { Boxes, LayoutDashboard, Workflow, Terminal, Settings } from "lucide-react";
import type { ReactNode } from "react";

interface NavItem {
  label: string;
  icon: ReactNode;
  hint: string;
}

// Navigation mirrors the frontend feature slices (catalog, canvas, console, admin).
// Routing is wired in M8; for now this is the shell that frames every surface.
const NAV: NavItem[] = [
  { label: "Dashboard", icon: <LayoutDashboard size={18} />, hint: "Operations overview" },
  { label: "Catalog", icon: <Boxes size={18} />, hint: "Approved building blocks" },
  { label: "Canvas", icon: <Workflow size={18} />, hint: "Visual orchestration" },
  { label: "Console", icon: <Terminal size={18} />, hint: "Live execution & logs" },
  { label: "Admin", icon: <Settings size={18} />, hint: "Governance & connectors" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "flex", height: "100%" }}>
      <aside
        style={{
          width: 232,
          borderRight: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          flexDirection: "column",
          padding: "18px 14px",
          gap: 6,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "4px 8px 18px" }}>
          <Workflow size={22} color="var(--color-accent)" />
          <span style={{ fontWeight: 700, letterSpacing: "0.5px" }}>NEXUS</span>
        </div>
        {NAV.map((item) => (
          <button
            key={item.label}
            title={item.hint}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "10px 12px",
              borderRadius: 8,
              border: "none",
              background: "transparent",
              color: "var(--text-muted)",
              cursor: "pointer",
              fontSize: "0.9rem",
              textAlign: "left",
            }}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
        <div style={{ marginTop: "auto", fontSize: "0.7rem", color: "var(--text-muted)" }}>
          Automation Control Plane
        </div>
      </aside>
      <main style={{ flex: 1, overflow: "auto" }}>{children}</main>
    </div>
  );
}

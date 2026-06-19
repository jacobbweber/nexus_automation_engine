import { Boxes, LayoutDashboard, LogOut, Settings, Terminal, Workflow } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "@/app/auth";

const NAV = [
  { to: "/", label: "Dashboard", icon: <LayoutDashboard size={18} />, end: true },
  { to: "/catalog", label: "Catalog", icon: <Boxes size={18} /> },
  { to: "/canvas", label: "Canvas", icon: <Workflow size={18} /> },
  { to: "/console", label: "Console", icon: <Terminal size={18} /> },
  { to: "/admin", label: "Admin", icon: <Settings size={18} /> },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
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
          gap: 4,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "4px 8px 18px" }}>
          <Workflow size={22} color="var(--color-accent)" />
          <span style={{ fontWeight: 700, letterSpacing: "0.5px" }}>NEXUS</span>
        </div>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "10px 12px",
              borderRadius: 8,
              textDecoration: "none",
              color: isActive ? "var(--text)" : "var(--text-muted)",
              background: isActive ? "var(--surface-2)" : "transparent",
              fontSize: "0.9rem",
            })}
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
        <div style={{ marginTop: "auto", fontSize: "0.78rem", color: "var(--text-muted)" }}>
          <div style={{ padding: "8px" }}>
            {user?.username} · <span style={{ color: "var(--color-accent)" }}>{user?.global_role}</span>
          </div>
          <button
            onClick={logout}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              width: "100%",
              padding: "8px",
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--text-muted)",
              cursor: "pointer",
            }}
          >
            <LogOut size={15} /> Sign out
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, overflow: "auto" }}>{children}</main>
    </div>
  );
}

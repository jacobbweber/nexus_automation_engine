import { AlertTriangle, Boxes, LayoutDashboard, Library, LogOut, ShieldCheck, Settings, Terminal, Workflow } from "lucide-react";
import { useEffect, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "@/app/auth";
import { useMode } from "@/shared/theme/mode";
import { ModeToggle } from "@/shared/theme/ModeToggle";
import { DisplayControls } from "@/shared/theme/DisplayControls";
import { ThemePicker } from "@/shared/theme/ThemePicker";

const NAV = [
  { to: "/", area: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} />, end: true },
  { to: "/catalog", area: "catalog", label: "Catalog", icon: <Boxes size={18} /> },
  { to: "/canvas", area: "canvas", label: "Canvas", icon: <Workflow size={18} /> },
  { to: "/library", area: "library", label: "Library", icon: <Library size={18} /> },
  { to: "/console", area: "console", label: "Console", icon: <Terminal size={18} /> },
  { to: "/incidents", area: "incidents", label: "Incidents", icon: <AlertTriangle size={18} /> },
  { to: "/governance", area: "governance", label: "Governance", icon: <ShieldCheck size={18} /> },
  { to: "/admin", area: "admin", label: "Admin", icon: <Settings size={18} /> },
];

/** Resolve the active area from the current path (longest matching nav prefix). */
function areaForPath(pathname: string): string {
  const match = NAV.filter((n) => n.to !== "/" && pathname.startsWith(n.to)).sort(
    (a, b) => b.to.length - a.to.length,
  )[0];
  return match?.area ?? "dashboard";
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const { setActiveArea } = useMode();
  const area = areaForPath(pathname);

  // Retint the chrome for the active surface + let the mode engine apply any per-area override.
  useEffect(() => {
    document.documentElement.dataset.area = area;
    setActiveArea(area);
    return () => setActiveArea(undefined);
  }, [area, setActiveArea]);

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
          <Workflow size={22} color="var(--area-accent)" />
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
              color: isActive ? "var(--area-accent-contrast)" : "var(--text-muted)",
              background: isActive ? "var(--area-accent)" : "transparent",
              fontSize: "0.9rem",
              transition: "background-color var(--dur-1) var(--ease-out)",
            })}
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
        <div style={{ marginTop: "auto", fontSize: "0.78rem", color: "var(--text-muted)" }}>
          <div style={{ padding: "8px 4px" }}>
            <ModeToggle />
          </div>
          <details style={{ padding: "0 4px 6px" }}>
            <summary style={{ cursor: "pointer", fontSize: "0.74rem", color: "var(--text-muted)", padding: "4px 2px" }}>
              Display &amp; accessibility
            </summary>
            <DisplayControls />
            <div style={{ marginTop: 8 }}>
              <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Theme</span>
              <div style={{ marginTop: 4 }}>
                <ThemePicker />
              </div>
              <NavLink to="/theme-studio" style={{ display: "inline-block", marginTop: 8, fontSize: "0.74rem", color: "var(--accent)" }}>
                Open Theme Studio →
              </NavLink>
            </div>
          </details>
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

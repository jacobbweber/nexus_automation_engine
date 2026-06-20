import {
  AlertTriangle,
  Boxes,
  ClipboardCheck,
  GaugeCircle,
  LayoutDashboard,
  Library,
  Lock,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  Settings,
  Terminal,
  Workflow,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "@/app/auth";
import { useMode } from "@/shared/theme/mode";
import { ModeToggle } from "@/shared/theme/ModeToggle";
import { DisplayControls } from "@/shared/theme/DisplayControls";
import { ThemePicker } from "@/shared/theme/ThemePicker";
import { CommandPalette } from "@/features/command-palette/CommandPalette";
import { NotificationsBell } from "@/features/notifications/NotificationsBell";
import { ConnectionBanner } from "@/shared/ui/ConnectionBanner";

const NAV = [
  { to: "/", area: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} />, end: true },
  { to: "/catalog", area: "catalog", label: "Catalog", icon: <Boxes size={18} /> },
  { to: "/canvas", area: "canvas", label: "Canvas", icon: <Workflow size={18} /> },
  { to: "/library", area: "library", label: "Library", icon: <Library size={18} /> },
  { to: "/console", area: "console", label: "Console", icon: <Terminal size={18} /> },
  { to: "/incidents", area: "incidents", label: "Incidents", icon: <AlertTriangle size={18} /> },
  { to: "/compliance", area: "governance", label: "Compliance", icon: <GaugeCircle size={18} /> },
  { to: "/approvals", area: "governance", label: "Approvals", icon: <ClipboardCheck size={18} /> },
  { to: "/determinism", area: "governance", label: "Guardrails", icon: <Lock size={18} /> },
  { to: "/governance", area: "governance", label: "Governance", icon: <ShieldCheck size={18} /> },
  { to: "/admin", area: "admin", label: "Admin", icon: <Settings size={18} /> },
];

function areaForPath(pathname: string): string {
  const match = NAV.filter((n) => n.to !== "/" && pathname.startsWith(n.to)).sort(
    (a, b) => b.to.length - a.to.length,
  )[0];
  return match?.area ?? "dashboard";
}

const COLLAPSE_KEY = "nexus_nav_collapsed";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const { setActiveArea } = useMode();
  const area = areaForPath(pathname);

  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSE_KEY) === "1");
  const linkRefs = useRef<(HTMLAnchorElement | null)[]>([]);

  useEffect(() => {
    document.documentElement.dataset.area = area;
    setActiveArea(area);
    return () => setActiveArea(undefined);
  }, [area, setActiveArea]);

  function toggleCollapsed() {
    setCollapsed((c) => {
      localStorage.setItem(COLLAPSE_KEY, c ? "0" : "1");
      return !c;
    });
  }

  // Arrow-key navigation between nav items (roving focus).
  function onNavKeyDown(e: React.KeyboardEvent, i: number) {
    const items = linkRefs.current.filter(Boolean);
    let next = -1;
    if (e.key === "ArrowDown") next = (i + 1) % items.length;
    else if (e.key === "ArrowUp") next = (i - 1 + items.length) % items.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = items.length - 1;
    if (next >= 0) {
      e.preventDefault();
      linkRefs.current[next]?.focus();
    }
  }

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <aside
        style={{
          width: collapsed ? 72 : 232,
          borderRight: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          flexDirection: "column",
          padding: "14px 12px",
          gap: 4,
          transition: "width var(--dur-2) var(--ease-out)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "4px 6px 14px" }}>
          <Workflow size={22} color="var(--area-accent)" />
          {!collapsed && <span style={{ fontWeight: 700, letterSpacing: "0.5px", flex: 1 }}>NEXUS</span>}
          <button
            onClick={toggleCollapsed}
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
            title={collapsed ? "Expand" : "Collapse"}
            style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex" }}
          >
            {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>

        <nav aria-label="Primary" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {NAV.map((item, i) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              ref={(el) => {
                linkRefs.current[i] = el;
              }}
              onKeyDown={(e) => onNavKeyDown(e, i)}
              title={collapsed ? item.label : undefined}
              style={({ isActive }) => ({
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "10px 12px",
                borderRadius: 8,
                textDecoration: "none",
                justifyContent: collapsed ? "center" : "flex-start",
                color: isActive ? "var(--area-accent-contrast)" : "var(--text-muted)",
                background: isActive ? "var(--area-accent)" : "transparent",
                fontSize: "0.9rem",
                transition: "background-color var(--dur-1) var(--ease-out)",
              })}
            >
              {item.icon}
              {!collapsed && item.label}
            </NavLink>
          ))}
        </nav>

        <div style={{ marginTop: "auto", fontSize: "0.78rem", color: "var(--text-muted)" }}>
          <div style={{ padding: "0 0 6px" }}>
            <NotificationsBell collapsed={collapsed} />
          </div>
          {!collapsed && (
            <>
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
                  <NavLink to="/theme-studio" style={{ display: "block", marginTop: 8, fontSize: "0.74rem", color: "var(--accent)" }}>
                    Open Theme Studio →
                  </NavLink>
                  <NavLink to="/accessibility" style={{ display: "block", marginTop: 6, fontSize: "0.74rem", color: "var(--accent)" }}>
                    Accessibility Center →
                  </NavLink>
                </div>
              </details>
              <div style={{ padding: "8px" }}>
                {user?.username} · <span style={{ color: "var(--area-accent)" }}>{user?.global_role}</span>
              </div>
            </>
          )}
          <button
            onClick={logout}
            aria-label="Sign out"
            title="Sign out"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: collapsed ? "center" : "flex-start",
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
            <LogOut size={15} /> {!collapsed && "Sign out"}
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, overflow: "auto" }}>
        <ConnectionBanner />
        {children}
      </main>
      <CommandPalette />
    </div>
  );
}

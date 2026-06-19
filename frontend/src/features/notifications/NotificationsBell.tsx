// Notifications bell + panel (C18). Non-blocking; polls existing endpoints, shows an unread count,
// and links each item to where it lives. Marks all seen on open (persisted).

import { Bell } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Canvas, Incidents, Jobs } from "@/shared/api/client";
import { buildNotifications, type Notif } from "./notifications";

const SEEN_KEY = "nexus_notif_seen";
const POLL_MS = 25_000;

function loadSeen(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

export function NotificationsBell({ collapsed }: { collapsed?: boolean }) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [notifs, setNotifs] = useState<Notif[]>([]);
  const [seen, setSeen] = useState<Set<string>>(loadSeen);
  const ref = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    const [board, reviews, jobs] = await Promise.all([
      Incidents.board().catch(() => ({})),
      Canvas.pendingReviews().catch(() => []),
      Jobs.list().catch(() => []),
    ]);
    setNotifs(buildNotifications(board, reviews, jobs));
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  // Close on outside click.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, [open]);

  const unread = useMemo(() => notifs.filter((n) => !seen.has(n.id)).length, [notifs, seen]);

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next && notifs.length) {
      const all = new Set([...seen, ...notifs.map((n) => n.id)]);
      setSeen(all);
      try {
        localStorage.setItem(SEEN_KEY, JSON.stringify([...all]));
      } catch {
        /* ignore */
      }
    }
  }

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        onClick={toggle}
        aria-label={`Notifications${unread ? ` (${unread} unread)` : ""}`}
        title="Notifications"
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
          position: "relative",
        }}
      >
        <span style={{ position: "relative", display: "flex" }}>
          <Bell size={15} />
          {unread > 0 && (
            <span
              aria-hidden
              style={{
                position: "absolute",
                top: -5,
                right: -6,
                minWidth: 14,
                height: 14,
                padding: "0 3px",
                borderRadius: 999,
                background: "var(--danger)",
                color: "#fff",
                fontSize: "0.6rem",
                lineHeight: "14px",
                textAlign: "center",
                fontWeight: 700,
              }}
            >
              {unread}
            </span>
          )}
        </span>
        {!collapsed && <span style={{ fontSize: "0.8rem" }}>Notifications</span>}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          style={{
            position: "absolute",
            bottom: "calc(100% + 6px)",
            left: 0,
            width: 320,
            maxHeight: "60vh",
            overflow: "auto",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            boxShadow: "var(--shadow-3)",
            zIndex: 1000,
          }}
        >
          <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", fontSize: "0.74rem", textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)" }}>
            Notifications
          </div>
          {notifs.length === 0 && (
            <div style={{ padding: "16px 14px", color: "var(--text-muted)", fontSize: "0.84rem" }}>You're all caught up.</div>
          )}
          {notifs.map((n) => (
            <button
              key={n.id}
              onClick={() => {
                navigate(n.to);
                setOpen(false);
              }}
              style={{ display: "block", width: "100%", textAlign: "left", padding: "10px 14px", border: "none", borderBottom: "1px solid var(--divider)", background: "transparent", color: "var(--text)", cursor: "pointer" }}
            >
              <div style={{ fontSize: "0.84rem", fontWeight: 500 }}>{n.title}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{n.detail}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

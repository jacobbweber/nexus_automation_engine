// Honest offline/degraded indicator (C19). Watches the browser online state and pings the API
// health endpoint; shows a calm, non-blocking banner when the backend is unreachable, and clears
// itself when the connection is restored. Never blocks interaction.

import { WifiOff } from "lucide-react";
import { useEffect, useState } from "react";
import { getHealth } from "@/shared/api/client";

const PING_MS = 20_000;

export function ConnectionBanner() {
  const [degraded, setDegraded] = useState(false);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      if (typeof navigator !== "undefined" && navigator.onLine === false) {
        if (alive) setDegraded(true);
        return;
      }
      try {
        await getHealth();
        if (alive) setDegraded(false);
      } catch {
        if (alive) setDegraded(true);
      }
    };
    check();
    const id = setInterval(check, PING_MS);
    const onOffline = () => setDegraded(true);
    const onOnline = () => check();
    window.addEventListener("offline", onOffline);
    window.addEventListener("online", onOnline);
    return () => {
      alive = false;
      clearInterval(id);
      window.removeEventListener("offline", onOffline);
      window.removeEventListener("online", onOnline);
    };
  }, []);

  if (!degraded) return null;
  return (
    <div
      role="status"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 16px",
        background: "var(--warn-soft)",
        color: "var(--text)",
        borderBottom: "1px solid var(--border)",
        fontSize: "0.82rem",
      }}
    >
      <WifiOff size={15} style={{ color: "var(--warn)" }} aria-hidden />
      Backend unreachable — showing the last loaded data and retrying. Actions may not save until the
      connection is restored.
    </div>
  );
}

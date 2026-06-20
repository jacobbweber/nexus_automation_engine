import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Jobs, openSocket, type Job } from "@/shared/api/client";
import { Button, Card, Page, StatusBadge } from "@/shared/ui/primitives";

interface LogLine {
  message: string;
  stream: string;
}

// eslint-disable-next-line no-control-regex -- strips ANSI SGR escape sequences from logs
const ANSI = /\x1b\[[0-9;]*m/g;

export function ConsolePage() {
  const [params] = useSearchParams();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [active, setActive] = useState<string | null>(params.get("job"));
  const [lines, setLines] = useState<LogLine[]>([]);
  const [status, setStatus] = useState<string>("");
  const [filter, setFilter] = useState("");
  const socketRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const cleanLines = useMemo(() => lines.map((l) => ({ ...l, message: l.message.replace(ANSI, "") })), [lines]);
  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    return q ? cleanLines.filter((l) => l.message.toLowerCase().includes(q)) : cleanLines;
  }, [cleanLines, filter]);

  function downloadLog() {
    const blob = new Blob([cleanLines.map((l) => l.message).join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `run-${active}.log`;
    a.click();
    URL.revokeObjectURL(url);
  }

  useEffect(() => {
    Jobs.list().then(setJobs).catch(() => setJobs([]));
  }, []);

  useEffect(() => {
    if (!active) return;
    setLines([]);
    setStatus("");
    Jobs.get(active).then((j) => setStatus(j.status)).catch(() => undefined);

    const ws = openSocket(`/jobs/${active}/stream`);
    socketRef.current = ws;
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "log") {
        setLines((prev) => [...prev, { message: data.message, stream: data.stream }]);
      } else if (data.type === "status") {
        setStatus(data.status);
      }
    };
    return () => ws.close();
  }, [active]);

  useEffect(() => {
    if (!filter) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines, filter]);

  return (
    <Page title="Execution Console" subtitle="Live, streamed run output">
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 14 }}>
        <Card style={{ maxHeight: "70vh", overflow: "auto" }}>
          {jobs.map((j) => (
            <button
              key={j.id}
              onClick={() => setActive(j.id)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "8px",
                marginBottom: 4,
                borderRadius: 8,
                border: "none",
                background: active === j.id ? "var(--surface-2)" : "transparent",
                color: "var(--text)",
                cursor: "pointer",
              }}
            >
              <div style={{ fontSize: "0.8rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {j.name}
              </div>
              <StatusBadge status={j.status} />
            </button>
          ))}
        </Card>
        <Card style={{ background: "#0b0e12", padding: 0, height: "70vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          {active ? (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                <span style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>
                  run {active} · <StatusBadge status={status || "…"} />
                </span>
                <input
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder="Filter log…"
                  aria-label="Filter log"
                  style={{ marginLeft: "auto", width: 200, padding: "5px 9px", borderRadius: "var(--radius-md)", border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.06)", color: "#e6eaef", fontSize: "0.76rem" }}
                />
                {filter && <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>{visible.length}/{cleanLines.length}</span>}
                <Button size="sm" variant="ghost" onClick={downloadLog}>Download</Button>
              </div>
              <div aria-live="polite" style={{ flex: 1, overflow: "auto", padding: "12px 14px", fontFamily: "ui-monospace, monospace", fontSize: "0.8rem" }}>
                {visible.map((l, i) => (
                  <div key={i} style={{ color: l.stream === "stderr" ? "#e08b7f" : "#cdd6e0", whiteSpace: "pre-wrap" }}>
                    {l.message}
                  </div>
                ))}
                {filter && visible.length === 0 && <span style={{ color: "var(--text-muted)" }}>No lines match “{filter}”.</span>}
                <div ref={bottomRef} />
              </div>
            </>
          ) : (
            <span style={{ color: "var(--text-muted)", padding: 16 }}>Select a run to stream its logs.</span>
          )}
        </Card>
      </div>
    </Page>
  );
}

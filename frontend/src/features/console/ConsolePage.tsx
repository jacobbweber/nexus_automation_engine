import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Jobs, openSocket, type Job } from "@/shared/api/client";
import { Card, Page, StatusBadge } from "@/shared/ui/primitives";

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
  const socketRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

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
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

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
        <Card style={{ background: "#0b0e12", fontFamily: "ui-monospace, monospace", fontSize: "0.8rem", height: "70vh", overflow: "auto" }}>
          {active ? (
            <>
              <div style={{ color: "var(--text-muted)", marginBottom: 8 }}>
                run {active} · <StatusBadge status={status || "…"} />
              </div>
              {lines.map((l, i) => (
                <div key={i} style={{ color: l.stream === "stderr" ? "#e08b7f" : "#cdd6e0", whiteSpace: "pre-wrap" }}>
                  {l.message.replace(ANSI, "")}
                </div>
              ))}
              <div ref={bottomRef} />
            </>
          ) : (
            <span style={{ color: "var(--text-muted)" }}>Select a run to stream its logs.</span>
          )}
        </Card>
      </div>
    </Page>
  );
}

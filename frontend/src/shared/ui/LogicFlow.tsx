// Animated SVG "logic flow" — a left-to-right phase diagram with flowing connectors and
// pulsing nodes. Used on the automation detail "Logic Flow" tab and (live) for canvas runs.

export interface FlowPhase {
  label: string;
  kind?: "start" | "action" | "gate" | "end";
  state?: "pending" | "running" | "completed" | "failed" | "skipped";
}

const KIND_COLOR: Record<string, string> = {
  start: "var(--color-accent)",
  action: "#d8a657",
  gate: "#c77b6e",
  end: "var(--color-ok)",
};
const STATE_COLOR: Record<string, string> = {
  running: "var(--color-accent)",
  completed: "var(--color-ok)",
  failed: "var(--color-danger)",
  skipped: "var(--text-muted)",
};

export function LogicFlow({ phases, animate = true }: { phases: FlowPhase[]; animate?: boolean }) {
  const W = 180;
  const GAP = 56;
  const H = 120;
  const nodeW = 140;
  const nodeH = 54;
  const totalW = phases.length * W + GAP;
  const cy = H / 2;

  return (
    <div style={{ overflowX: "auto", padding: "8px 0" }}>
      <svg width={totalW} height={H} style={{ display: "block" }}>
        <defs>
          <style>{`
            @keyframes nexusDash { to { stroke-dashoffset: -24; } }
            @keyframes nexusPulse { 0%,100% { opacity: 1 } 50% { opacity: .55 } }
            .flow-line { stroke-dasharray: 6 6; ${animate ? "animation: nexusDash 1s linear infinite;" : ""} }
            .flow-running { animation: nexusPulse 1.1s ease-in-out infinite; }
          `}</style>
        </defs>
        {phases.map((p, i) => {
          const x = i * W + 10;
          const color = p.state ? STATE_COLOR[p.state] ?? KIND_COLOR[p.kind ?? "action"]
            : KIND_COLOR[p.kind ?? "action"];
          const nextX = x + nodeW;
          return (
            <g key={i}>
              {i < phases.length - 1 && (
                <line
                  className={"flow-line" + (p.state === "running" ? " flow-running" : "")}
                  x1={nextX} y1={cy} x2={nextX + GAP - 4} y2={cy}
                  stroke="var(--text-muted)" strokeWidth={2}
                />
              )}
              {i < phases.length - 1 && (
                <polygon
                  points={`${nextX + GAP - 6},${cy - 4} ${nextX + GAP + 2},${cy} ${nextX + GAP - 6},${cy + 4}`}
                  fill="var(--text-muted)"
                />
              )}
              <rect
                className={p.state === "running" ? "flow-running" : ""}
                x={x} y={cy - nodeH / 2} width={nodeW} height={nodeH} rx={10}
                fill="var(--surface)" stroke={color} strokeWidth={2}
              />
              <circle cx={x + 14} cy={cy - nodeH / 2 + 14} r={4} fill={color} />
              <text x={x + nodeW / 2} y={cy + 5} textAnchor="middle"
                    fill="var(--text)" fontSize="12" fontWeight="600">
                {p.label.length > 18 ? p.label.slice(0, 17) + "…" : p.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

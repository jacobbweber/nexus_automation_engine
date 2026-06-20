// CI health badge — a compact status + score pill. Status is conveyed by text + colour (never
// colour alone), consistent with the protected-status accessibility rule.

const COLOR: Record<string, string> = {
  healthy: "var(--success)",
  degraded: "var(--warn)",
  unhealthy: "var(--danger)",
};

export function HealthBadge({
  status,
  score,
  size = "md",
}: {
  status: string;
  score?: number;
  size?: "sm" | "md";
}) {
  const color = COLOR[status] ?? "var(--text-muted)";
  const pad = size === "sm" ? "1px 6px" : "2px 9px";
  const font = size === "sm" ? "0.66rem" : "0.72rem";
  return (
    <span
      title={`CI health: ${status}${score != null ? ` (${score}/100)` : ""}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: pad,
        borderRadius: 999,
        fontSize: font,
        fontWeight: 600,
        color,
        border: `1px solid ${color}`,
        background: `color-mix(in srgb, ${color} 12%, transparent)`,
        whiteSpace: "nowrap",
      }}
    >
      <span
        aria-hidden
        style={{ width: 7, height: 7, borderRadius: 999, background: color, display: "inline-block" }}
      />
      {status}
      {score != null && <span style={{ opacity: 0.8 }}>{score}</span>}
    </span>
  );
}

// Multi-audience Change Review Packet viewer (M26.6). A Technical / Non-technical / Executive
// toggle re-renders the same packet for the right reader; the flowchart is always available.
// Executive/non-technical views deliberately hide connectors/params and show plain outcomes.

import { useState } from "react";
import type { ReviewPacket } from "@/shared/api/client";
import { LogicFlow, type FlowPhase } from "@/shared/ui/LogicFlow";

type Audience = "technical" | "non_technical" | "executive";

const CLASS_COLOR: Record<string, string> = {
  standard: "var(--success)",
  normal: "var(--warn)",
  emergency: "var(--danger)",
};

export function ReviewPacketView({ packet }: { packet: ReviewPacket }) {
  const [audience, setAudience] = useState<Audience>("non_technical");
  const classColor = CLASS_COLOR[packet.change_class] ?? "var(--text-muted)";
  const phases: FlowPhase[] = packet.flowchart.map((p) => ({
    label: p.label,
    kind: (p.kind as FlowPhase["kind"]) ?? "action",
  }));

  return (
    <div>
      {/* headline */}
      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 8 }}>
        <strong style={{ fontSize: "1rem" }}>{packet.workflow_name}</strong>
        <span style={pill(classColor)}>{packet.change_class}</span>
        <span style={pill("var(--text-muted)")}>review: {packet.required_level}</span>
        <span style={pill("var(--text-muted)")}>risk: {packet.risk}</span>
        {packet.blast_radius > 0 && (
          <span style={pill("var(--text-muted)")}>{packet.blast_radius} CI(s)</span>
        )}
      </div>

      {/* audience toggle */}
      <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
        {(
          [
            ["technical", "Technical"],
            ["non_technical", "Non-technical"],
            ["executive", "Executive"],
          ] as [Audience, string][]
        ).map(([a, label]) => (
          <button
            key={a}
            onClick={() => setAudience(a)}
            style={{
              padding: "5px 12px",
              borderRadius: 999,
              border: "1px solid var(--border)",
              cursor: "pointer",
              fontSize: "0.8rem",
              background: audience === a ? "var(--accent)" : "transparent",
              color: audience === a ? "var(--accent-contrast)" : "var(--text)",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {audience === "technical" ? (
        <table style={{ width: "100%", fontSize: "0.8rem", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--text-muted)" }}>
              <th style={th}>Step</th>
              <th style={th}>Connector</th>
              <th style={th}>Action</th>
              <th style={th}>Params</th>
              <th style={th}>Idempotency</th>
            </tr>
          </thead>
          <tbody>
            {packet.technical.map((t, i) => (
              <tr key={t.node_id || i}>
                <td style={td}>{i + 1}. {t.name}</td>
                <td style={td}>{t.connector}</td>
                <td style={td}>{t.action}</td>
                <td style={{ ...td, fontFamily: "var(--font-mono)", fontSize: "0.74rem" }}>
                  {JSON.stringify(t.params)}
                </td>
                <td style={td}>{t.idempotency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div style={{ fontSize: "0.88rem" }}>
          <p style={{ marginTop: 0 }}>{packet.summary}</p>
          <ol style={{ paddingLeft: 18 }}>
            {packet.narrative.map((n) => (
              <li key={n.step} style={{ marginBottom: 3 }}>
                {n.text}
              </li>
            ))}
          </ol>
          {packet.rollback && (
            <p>
              <strong>Rollback:</strong> {packet.rollback}
            </p>
          )}
          {audience === "executive" && packet.reasons.length > 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>
              Why review is required: {packet.reasons.join("; ")}.
            </p>
          )}
        </div>
      )}

      <div style={{ marginTop: 14 }}>
        <div style={{ fontSize: "0.7rem", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 4 }}>
          Flow
        </div>
        <LogicFlow phases={phases} animate={false} />
      </div>
    </div>
  );
}

function pill(color: string): React.CSSProperties {
  return {
    fontSize: "0.7rem",
    fontWeight: 600,
    padding: "2px 9px",
    borderRadius: 999,
    color,
    border: `1px solid ${color}`,
    background: `color-mix(in srgb, ${color} 12%, transparent)`,
  };
}
const th: React.CSSProperties = { padding: "3px 8px", fontWeight: 600 };
const td: React.CSSProperties = { padding: "3px 8px", borderTop: "1px solid var(--border)", verticalAlign: "top" };

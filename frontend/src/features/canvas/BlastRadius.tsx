// Blast-radius preview (E25): for a node targeting a literal CI, shows which CMDB CIs an action
// would touch (the target + cluster siblings) before the operator runs it.

import { useEffect, useState } from "react";
import { Connectors, type ImpactItem } from "@/shared/api/client";

export function BlastRadius({ targets }: { targets: string[] }) {
  const [impact, setImpact] = useState<ImpactItem[] | null>(null);
  const key = targets.join(",");

  useEffect(() => {
    if (targets.length === 0) {
      setImpact(null);
      return;
    }
    Connectors.impact(targets).then(setImpact).catch(() => setImpact([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  if (targets.length === 0 || impact === null) return null;

  return (
    <div style={{ marginTop: 12, padding: "10px 12px", borderRadius: "var(--radius-md)", background: "var(--warn-soft)", border: "1px solid var(--border)" }}>
      <div style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 6 }}>
        Blast radius
      </div>
      {impact.length === 0 ? (
        <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>No matching CI in the CMDB.</div>
      ) : (
        <>
          <div style={{ fontSize: "0.78rem", marginBottom: 4 }}>
            {impact.length} CI{impact.length === 1 ? "" : "s"} affected
          </div>
          {impact.map((i) => (
            <div key={i.name} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.74rem", padding: "1px 0" }}>
              <span>{i.name}</span>
              <span style={{ color: "var(--text-muted)" }}>{i.reason}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

// Change calendar (J39): an agenda of CHG records pulled from the simulated ServiceNow CMDB,
// grouped by day, with overlap-on-shared-CI conflict flags.

import { AlertTriangle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Connectors, type ServiceNowChange } from "@/shared/api/client";
import { Card, StatusBadge } from "@/shared/ui/primitives";
import { EmptyState } from "@/shared/ui/EmptyState";
import { conflictedNumbers, detectConflicts, groupByDay } from "./changeConflicts";

export function ChangeCalendar() {
  const [changes, setChanges] = useState<ServiceNowChange[]>([]);

  useEffect(() => {
    Connectors.changes().then(setChanges).catch(() => setChanges([]));
  }, []);

  const conflicts = useMemo(() => detectConflicts(changes), [changes]);
  const conflicted = useMemo(() => conflictedNumbers(conflicts), [conflicts]);
  const days = useMemo(() => groupByDay(changes), [changes]);

  return (
    <Card>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
        <h2 style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>
          Change calendar
        </h2>
        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
          from ServiceNow CMDB (simulated)
        </span>
        {conflicts.length > 0 && (
          <span style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 5, color: "var(--warn)", fontSize: "0.78rem", fontWeight: 600 }}>
            <AlertTriangle size={14} /> {conflicts.length} window conflict{conflicts.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {changes.length === 0 && <EmptyState title="No upcoming changes" description="Approved CHGs from the CMDB appear here." />}

      {days.map(([day, items]) => (
        <div key={day} style={{ marginTop: 12 }}>
          <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>{day}</div>
          {items.map((c) => {
            const inConflict = conflicted.has(c.number);
            return (
              <div
                key={c.number}
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderTop: "1px solid var(--border)" }}
              >
                <span style={{ width: 96, fontSize: "0.74rem", color: "var(--text-muted)" }}>
                  {new Date(c.start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}–
                  {new Date(c.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                <span style={{ flex: 1 }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--text-muted)" }}>{c.number}</span>{" "}
                  {c.short_description}
                  {c.affected_cis.length > 0 && (
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}> · {c.affected_cis.join(", ")}</span>
                  )}
                </span>
                {inConflict && (
                  <span title="Window overlaps another change on a shared CI" style={{ color: "var(--warn)", display: "flex" }}>
                    <AlertTriangle size={14} />
                  </span>
                )}
                <span style={{ width: 90, textAlign: "right" }}><StatusBadge status={c.state} /></span>
                <span style={{ width: 80, textAlign: "right", fontSize: "0.72rem", color: "var(--text-muted)" }}>{c.assignment_group}</span>
              </div>
            );
          })}
        </div>
      ))}
    </Card>
  );
}

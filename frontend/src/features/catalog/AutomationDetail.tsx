import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Catalog, Compliance, type DriftReport, type Template } from "@/shared/api/client";
import { Button } from "@/shared/ui/primitives";
import { Markdown } from "@/shared/ui/Markdown";
import { LogicFlow, type FlowPhase } from "@/shared/ui/LogicFlow";
import { DriftReportView } from "@/shared/ui/DriftReportView";

type Tab = "overview" | "parameters" | "flow";

function phasesFor(t: Template): FlowPhase[] {
  const risky = t.risk === "high" || t.risk === "critical";
  const action: FlowPhase = { label: t.action.replace(/_/g, " "), kind: "action" };
  if (t.atomic) {
    return [
      { label: "Start", kind: "start" },
      ...(risky ? [{ label: "Approval", kind: "gate" as const }] : []),
      action,
      { label: "Complete", kind: "end" },
    ];
  }
  return [
    { label: "Start", kind: "start" },
    { label: "Plan / Dry-run", kind: "action" },
    ...(risky ? [{ label: "Approval", kind: "gate" as const }] : []),
    { label: t.action.replace(/_/g, " "), kind: "action" },
    { label: "Verify", kind: "action" },
    { label: "Complete", kind: "end" },
  ];
}

export function AutomationDetail({ template, onClose }: { template: Template; onClose: () => void }) {
  const [tab, setTab] = useState<Tab>("overview");
  const navigate = useNavigate();
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [checkMode, setCheckMode] = useState(template.supports_check_mode);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drift, setDrift] = useState<DriftReport | null>(null);

  async function checkCompliance() {
    setError(null);
    setDrift(null);
    try {
      setDrift(await Compliance.template(template.id, answers));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compliance check failed.");
    }
  }

  const missing = template.survey
    .filter((f) => f.required && !answers[f.name])
    .map((f) => f.label);

  async function run() {
    if (missing.length > 0) {
      setTab("parameters");
      setError(`Fill required parameter${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await Catalog.execute(template.id, answers, checkMode);
      navigate(`/console?job=${res.job_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed to dispatch.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div onClick={onClose} style={overlay}>
      <div onClick={(e) => e.stopPropagation()} style={drawer}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
          <div>
            <div style={{ fontSize: "0.66rem", textTransform: "uppercase", color: "var(--color-accent)" }}>
              {template.vendor} · {template.domain}
            </div>
            <h2 style={{ margin: "4px 0" }}>{template.name}</h2>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              v{template.version} · owner {template.owner} · ~{template.estimated_minutes}m ·{" "}
              risk <strong style={{ color: "var(--text)" }}>{template.risk}</strong> ·{" "}
              {template.atomic ? "atomic" : "orchestrated"}
            </div>
            <div style={{ marginTop: 6 }}>
              <IdempotencyChip value={template.idempotency} />
            </div>
          </div>
          <Button variant="ghost" onClick={onClose}>✕</Button>
        </div>

        <div style={{ display: "flex", gap: 4, margin: "16px 0", borderBottom: "1px solid var(--border)" }}>
          {(["overview", "parameters", "flow"] as Tab[]).map((tb) => (
            <button key={tb} onClick={() => setTab(tb)} style={{
              padding: "8px 12px", border: "none", background: "transparent", cursor: "pointer",
              fontSize: "0.85rem", textTransform: "capitalize",
              color: tab === tb ? "var(--text)" : "var(--text-muted)",
              borderBottom: tab === tb ? "2px solid var(--color-accent)" : "2px solid transparent",
            }}>
              {tb === "flow" ? "Logic Flow" : tb}
            </button>
          ))}
        </div>

        <div style={{ flex: 1, overflow: "auto", minHeight: 200 }}>
          {tab === "overview" && (
            <>
              <Markdown source={template.markdown_documentation || template.description} />
              {template.prerequisites && (
                <div style={{ marginTop: 14, padding: 12, borderRadius: 8, background: "var(--surface-2)" }}>
                  <div style={{ fontSize: "0.7rem", textTransform: "uppercase", color: "var(--text-muted)" }}>Prerequisites</div>
                  <div style={{ fontSize: "0.85rem", marginTop: 4 }}>{template.prerequisites}</div>
                </div>
              )}
              {template.tags.length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 12 }}>
                  {template.tags.map((tag) => (
                    <span key={tag} style={{ fontSize: "0.7rem", padding: "2px 8px", borderRadius: 12, background: "var(--surface-2)", color: "var(--text-muted)" }}>
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}

          {tab === "parameters" && (
            <div>
              {template.survey.length === 0 && (
                <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No parameters.</div>
              )}
              {template.survey.map((f) => (
                <label key={f.name} style={{ display: "block", margin: "10px 0" }}>
                  <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    {f.label}{f.required ? " *" : ""}
                    {f.source && <span style={{ color: "var(--color-accent)" }}> · {f.source}</span>}
                  </span>
                  {f.choices ? (
                    <select onChange={(e) => setAnswers((a) => ({ ...a, [f.name]: e.target.value }))} style={ctl}>
                      <option value="">—</option>
                      {f.choices.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  ) : (
                    <input onChange={(e) => setAnswers((a) => ({ ...a, [f.name]: e.target.value }))} style={ctl} />
                  )}
                </label>
              ))}
            </div>
          )}

          {tab === "flow" && (
            <div>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                How this automation flows when executed:
              </p>
              <LogicFlow phases={phasesFor(template)} />
            </div>
          )}
        </div>

        {/* Run bar */}
        {error && (
          <div role="alert" style={{
            marginTop: 10, padding: "8px 12px", borderRadius: 8, fontSize: "0.8rem",
            background: "color-mix(in srgb, var(--danger) 12%, transparent)",
            border: "1px solid var(--danger)", color: "var(--danger)",
          }}>
            {error}
          </div>
        )}
        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 14, marginTop: 10, display: "flex", alignItems: "center", gap: 12 }}>
          {template.supports_check_mode && (
            <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: "0.82rem" }}>
              <input type="checkbox" checked={checkMode} onChange={(e) => setCheckMode(e.target.checked)} />
              Check mode
            </label>
          )}
          <div style={{ marginLeft: "auto", display: "flex", gap: 10 }}>
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button variant="ghost" onClick={checkCompliance}>Check compliance</Button>
            <Button onClick={run} disabled={busy}>{busy ? "Dispatching…" : "Run"}</Button>
          </div>
        </div>
        {drift && (
          <div style={{ marginTop: 12, maxHeight: 260, overflow: "auto" }}>
            <DriftReportView report={drift} />
          </div>
        )}
      </div>
    </div>
  );
}

// Idempotency contract chip — re-run safety surfaced on the building block (v4.0 §3).
const IDEMPOTENCY_META: Record<string, { label: string; color: string }> = {
  idempotent: { label: "idempotent · safe to re-run", color: "var(--success)" },
  check_only: { label: "check-only · never mutates", color: "var(--info)" },
  non_idempotent: { label: "non-idempotent · guard re-runs", color: "var(--warn)" },
};

function IdempotencyChip({ value }: { value: string }) {
  const meta = IDEMPOTENCY_META[value] ?? { label: value, color: "var(--text-muted)" };
  return (
    <span
      title="Idempotency class — whether this automation is safe to re-run for compliance"
      style={{
        fontSize: "0.7rem",
        fontWeight: 600,
        padding: "2px 9px",
        borderRadius: 999,
        color: meta.color,
        border: `1px solid ${meta.color}`,
        background: `color-mix(in srgb, ${meta.color} 12%, transparent)`,
      }}
    >
      {meta.label}
    </span>
  );
}

const overlay: React.CSSProperties = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "flex", justifyContent: "flex-end", zIndex: 50,
};
const drawer: React.CSSProperties = {
  width: 480, height: "100%", background: "var(--surface)", borderLeft: "1px solid var(--border)",
  padding: 24, display: "flex", flexDirection: "column", boxSizing: "border-box",
};
const ctl: React.CSSProperties = {
  width: "100%", marginTop: 4, padding: "8px 10px", borderRadius: 8,
  border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box",
};

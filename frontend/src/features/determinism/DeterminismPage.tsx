// Determinism / Guardrails management page (M27.5) — declare what is guaranteed about the estate
// (pinning rules) and see where reality matches (coverage). Admins author rules; everyone sees
// coverage. Selector builder is schema-driven (CI types from the CMDB schema registry).

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  type CITypeSchema,
  Cmdb,
  type Coverage,
  Determinism,
  type PinningRule,
  type Workflow,
  Canvas,
} from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Button, Card, Page } from "@/shared/ui/primitives";

const TRIGGERS = ["on_create", "on_change", "on_schedule", "on_demand"];
const ENFORCEMENTS = ["assert", "enforce", "gate"];
const ENF_COLOR: Record<string, string> = {
  assert: "var(--info)",
  enforce: "var(--warn)",
  gate: "var(--danger)",
};

const ctl: React.CSSProperties = {
  padding: "5px 8px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
  fontSize: "0.82rem",
};

export function DeterminismPage() {
  const { user } = useAuth();
  const isAdmin = user?.global_role === "admin";
  const [rules, setRules] = useState<PinningRule[]>([]);
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [schemas, setSchemas] = useState<CITypeSchema[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [editing, setEditing] = useState<PinningRule | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    Determinism.rules().then(setRules).catch(() => setRules([]));
    Determinism.coverage().then(setCoverage).catch(() => setCoverage(null));
  }, []);

  useEffect(() => {
    load();
    Cmdb.schemas().then(setSchemas).catch(() => undefined);
    Canvas.list().then(setWorkflows).catch(() => undefined);
  }, [load]);

  function newRule() {
    setEditing({
      id: `pin_${Date.now().toString(36)}`,
      name: "",
      enabled: true,
      priority: 100,
      selector: { ci_type: null, tag_predicates: {}, field_predicates: {} },
      workflow: "",
      trigger: "on_schedule",
      enforcement: "assert",
      description: "",
    });
  }

  async function save() {
    if (!editing) return;
    setError(null);
    try {
      await Determinism.saveRule(editing);
      setEditing(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Save failed.");
    }
  }

  async function toggle(rule: PinningRule) {
    await Determinism.saveRule({ ...rule, enabled: !rule.enabled }).catch(() => undefined);
    load();
  }

  async function remove(id: string) {
    await Determinism.deleteRule(id).catch(() => undefined);
    load();
  }

  const covById = new Map((coverage?.rules ?? []).map((c) => [c.rule_id, c]));

  return (
    <Page title="Determinism & Guardrails" subtitle="What is guaranteed about the estate — and where reality differs">
      {error && (
        <div role="alert" style={{ color: "var(--danger)", marginBottom: 10, fontSize: "0.85rem" }}>
          {error}
        </div>
      )}

      {isAdmin && !editing && (
        <div style={{ marginBottom: 12 }}>
          <Button onClick={newRule}>+ New pinning rule</Button>
        </div>
      )}

      {editing && (
        <Card style={{ marginBottom: 14 }}>
          <h2 style={{ fontSize: "0.95rem", marginTop: 0 }}>Pinning rule</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Name">
              <input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} style={{ ...ctl, width: "100%" }} />
            </Field>
            <Field label="Guaranteed workflow">
              <select value={editing.workflow} onChange={(e) => setEditing({ ...editing, workflow: e.target.value })} style={{ ...ctl, width: "100%" }}>
                <option value="">— pick a workflow —</option>
                {workflows.map((w) => (
                  <option key={w.id} value={w.name}>{w.name}</option>
                ))}
              </select>
            </Field>
            <Field label="CI type (selector)">
              <select
                value={editing.selector.ci_type ?? ""}
                onChange={(e) => setEditing({ ...editing, selector: { ...editing.selector, ci_type: e.target.value || null } })}
                style={{ ...ctl, width: "100%" }}
              >
                <option value="">— any —</option>
                {schemas.map((s) => (
                  <option key={s.type} value={s.type}>{s.type}</option>
                ))}
              </select>
            </Field>
            <Field label="Tag predicate (tag=value, comma-sep)">
              <input
                defaultValue={Object.entries(editing.selector.tag_predicates).map(([k, v]) => `${k}=${v}`).join(", ")}
                onBlur={(e) => setEditing({ ...editing, selector: { ...editing.selector, tag_predicates: parsePreds(e.target.value) } })}
                placeholder="DR-Tier=0"
                style={{ ...ctl, width: "100%" }}
              />
            </Field>
            <Field label="Trigger">
              <select value={editing.trigger} onChange={(e) => setEditing({ ...editing, trigger: e.target.value })} style={{ ...ctl, width: "100%" }}>
                {TRIGGERS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </Field>
            <Field label="Enforcement">
              <select value={editing.enforcement} onChange={(e) => setEditing({ ...editing, enforcement: e.target.value })} style={{ ...ctl, width: "100%" }}>
                {ENFORCEMENTS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </Field>
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <Button onClick={save}>Save rule</Button>
            <Button variant="ghost" onClick={() => setEditing(null)}>Cancel</Button>
          </div>
        </Card>
      )}

      {rules.map((rule) => {
        const cov = covById.get(rule.id);
        return (
          <Card key={rule.id} style={{ marginBottom: 10, opacity: rule.enabled ? 1 : 0.55 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <strong style={{ fontSize: "0.9rem" }}>{rule.name}</strong>
              <span style={pill(ENF_COLOR[rule.enforcement] ?? "var(--text-muted)")}>{rule.enforcement}</span>
              <span style={pill("var(--text-muted)")}>{rule.trigger}</span>
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                {rule.selector.ci_type ?? "any"}
                {Object.entries(rule.selector.tag_predicates).map(([k, v]) => ` · ${k}=${v}`)}
                {" → "}{rule.workflow}
              </span>
              {isAdmin && (
                <span style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                  <button onClick={() => toggle(rule)} style={linkBtn}>{rule.enabled ? "disable" : "enable"}</button>
                  <button onClick={() => setEditing(rule)} style={linkBtn}>edit</button>
                  <button onClick={() => remove(rule.id)} style={{ ...linkBtn, color: "var(--danger)" }}>delete</button>
                </span>
              )}
            </div>
            {cov && (
              <div style={{ marginTop: 8, fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", gap: 14, flexWrap: "wrap" }}>
                <span><strong style={{ color: "var(--text)" }}>{cov.matched}</strong> CIs guaranteed</span>
                {rule.enforcement === "assert" && (
                  <>
                    <span style={{ color: "var(--success)" }}>{cov.compliant} compliant</span>
                    <span style={{ color: "var(--warn)" }}>{cov.drifted} drifted</span>
                  </>
                )}
                {!cov.workflow_exists && (
                  <span style={{ color: "var(--danger)" }}>⚠ workflow "{rule.workflow}" not found</span>
                )}
              </div>
            )}
          </Card>
        );
      })}

      {rules.length === 0 && (
        <Card>
          <p style={{ color: "var(--text-muted)", margin: 0 }}>
            No pinning rules yet. {isAdmin ? "Create one to guarantee a workflow for matching CIs." : ""}
          </p>
        </Card>
      )}
    </Page>
  );
}

function parsePreds(raw: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const part of raw.split(",")) {
    const [k, v] = part.split("=").map((s) => s.trim());
    if (k && v) out[k] = v;
  }
  return out;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "block" }}>
      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{label}</span>
      <div style={{ marginTop: 3 }}>{children}</div>
    </label>
  );
}
function pill(color: string): React.CSSProperties {
  return { fontSize: "0.7rem", fontWeight: 600, padding: "2px 8px", borderRadius: 999, color, border: `1px solid ${color}`, background: `color-mix(in srgb, ${color} 12%, transparent)` };
}
const linkBtn: React.CSSProperties = { background: "none", border: "none", color: "var(--accent)", cursor: "pointer", fontSize: "0.78rem" };

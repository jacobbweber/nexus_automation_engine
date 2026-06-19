import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Catalog, type Template } from "@/shared/api/client";
import { Button, Card, Page, StatusBadge } from "@/shared/ui/primitives";

export function CatalogPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selected, setSelected] = useState<Template | null>(null);

  useEffect(() => {
    Catalog.list().then(setTemplates).catch(() => setTemplates([]));
  }, []);

  return (
    <Page title="Service Automation Catalog" subtitle="Approved building blocks across all engines">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
        {templates.map((t) => (
          <Card key={t.id} style={{ cursor: "pointer" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
              <span style={{ fontSize: "0.7rem", textTransform: "uppercase", color: "var(--color-accent)" }}>
                {t.connector}
              </span>
              <StatusBadge status={t.approval_state} />
            </div>
            <h3 style={{ fontSize: "1rem", margin: "8px 0 6px" }}>{t.name}</h3>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", minHeight: 38 }}>
              {t.description}
            </p>
            <Button onClick={() => setSelected(t)}>Configure & run</Button>
          </Card>
        ))}
        {templates.length === 0 && (
          <Card>
            <span style={{ color: "var(--text-muted)" }}>No approved templates yet.</span>
          </Card>
        )}
      </div>
      {selected && <RunDrawer template={selected} onClose={() => setSelected(null)} />}
    </Page>
  );
}

function RunDrawer({ template, onClose }: { template: Template; onClose: () => void }) {
  const navigate = useNavigate();
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [checkMode, setCheckMode] = useState(template.supports_check_mode);
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    try {
      const res = await Catalog.execute(template.id, answers, checkMode);
      navigate(`/console?job=${res.job_id}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "flex", justifyContent: "flex-end" }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 420, height: "100%", background: "var(--surface)", borderLeft: "1px solid var(--border)", padding: 24, overflow: "auto" }}
      >
        <h2 style={{ marginTop: 0 }}>{template.name}</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{template.description}</p>
        {template.survey.map((f) => (
          <label key={f.name} style={{ display: "block", margin: "12px 0" }}>
            <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
              {f.label}
              {f.required ? " *" : ""}
            </span>
            {f.choices ? (
              <select
                onChange={(e) => setAnswers((a) => ({ ...a, [f.name]: e.target.value }))}
                style={inputStyle}
              >
                <option value="">—</option>
                {f.choices.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            ) : (
              <input
                onChange={(e) => setAnswers((a) => ({ ...a, [f.name]: e.target.value }))}
                style={inputStyle}
              />
            )}
            {f.source && (
              <span style={{ fontSize: "0.7rem", color: "var(--color-accent)" }}>
                dynamic source: {f.source}
              </span>
            )}
          </label>
        ))}
        {template.supports_check_mode && (
          <label style={{ display: "flex", gap: 8, alignItems: "center", margin: "14px 0", fontSize: "0.85rem" }}>
            <input type="checkbox" checked={checkMode} onChange={(e) => setCheckMode(e.target.checked)} />
            Check mode (dry run)
          </label>
        )}
        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
          <Button onClick={run} disabled={busy}>{busy ? "Dispatching…" : "Run"}</Button>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
        </div>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  marginTop: 4,
  padding: "8px 10px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
  boxSizing: "border-box",
};

// CMDB Schema Studio (M24.6) — admin surface to define/edit CI type schemas + lineage, validated
// deterministically on save by the backend (no AI). Mirrors Theme Studio's author→validate→save loop.

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  Cmdb,
  type CITypeSchema,
  type CmdbFieldDef,
  type LineageRelationship,
  type LineageSpec,
} from "@/shared/api/client";
import { Button } from "@/shared/ui/primitives";

const DATATYPES = ["string", "integer", "boolean", "enum", "datetime", "reference"];
const DIRECTIONS = ["up", "down"];
const CARDINALITIES = ["one", "many"];

const ctl: React.CSSProperties = {
  width: "100%",
  padding: "6px 8px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
  boxSizing: "border-box",
  fontSize: "0.82rem",
};

function emptyField(): CmdbFieldDef {
  return {
    name: "",
    label: "",
    datatype: "string",
    required: false,
    allowed_values: null,
    regex: null,
    default: null,
    sensitive: false,
  };
}

export function CmdbSchemaPage() {
  const [types, setTypes] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [schema, setSchema] = useState<CITypeSchema | null>(null);
  const [lineage, setLineage] = useState<LineageSpec | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const loadList = useCallback(() => {
    Cmdb.schemas()
      .then((list) => {
        setTypes(list.map((s) => s.type));
        if (!selected && list.length) setSelected(list[0].type);
      })
      .catch(() => undefined);
  }, [selected]);

  useEffect(() => {
    loadList();
  }, [loadList]);

  useEffect(() => {
    if (!selected) return;
    setError(null);
    setOk(null);
    Cmdb.schema(selected).then(setSchema).catch(() => setSchema(null));
    Cmdb.lineageFor(selected)
      .then(setLineage)
      .catch(() => setLineage({ type: selected, relationships: [] }));
  }, [selected]);

  function patchField(i: number, patch: Partial<CmdbFieldDef>) {
    if (!schema) return;
    const fields = schema.fields.map((f, idx) => (idx === i ? { ...f, ...patch } : f));
    setSchema({ ...schema, fields });
  }

  function patchRel(i: number, patch: Partial<LineageRelationship>) {
    if (!lineage) return;
    const relationships = lineage.relationships.map((r, idx) =>
      idx === i ? { ...r, ...patch } : r,
    );
    setLineage({ ...lineage, relationships });
  }

  async function save() {
    if (!schema || !lineage) return;
    setError(null);
    setOk(null);
    try {
      await Cmdb.saveSchema(schema.type, schema);
      await Cmdb.saveLineage(lineage.type, lineage);
      setOk("Saved — schema and lineage validated and stored.");
      loadList();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Save failed.");
    }
  }

  function newType() {
    const t = window.prompt("New CI type id (e.g. 'firewall'):", "");
    if (!t) return;
    const type = t.trim().toLowerCase();
    setSchema({
      type,
      label: type,
      version: 1,
      description: "",
      fields: [{ ...emptyField(), name: "name", label: "Name", required: true }],
      required_tags: ["owner", "team"],
      naming_pattern: null,
      updated_by: "",
      updated_at: "",
    });
    setLineage({ type, relationships: [] });
    setSelected(type);
    setTypes((ts) => (ts.includes(type) ? ts : [...ts, type]));
  }

  return (
    <div style={{ display: "flex", gap: 20 }}>
      <aside style={{ width: 200, flexShrink: 0 }}>
        <h1 style={{ fontSize: "1.2rem", margin: "0 0 4px" }}>CMDB Schema Studio</h1>
        <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 0 }}>
          Define what each CI type must contain — validated deterministically.
        </p>
        <Button onClick={newType} variant="ghost">
          + New CI type
        </Button>
        <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 2 }}>
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setSelected(t)}
              style={{
                textAlign: "left",
                padding: "7px 10px",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                fontSize: "0.85rem",
                background: t === selected ? "var(--accent-soft)" : "transparent",
                color: "var(--text)",
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </aside>

      <main style={{ flex: 1, minWidth: 0 }}>
        {schema && lineage ? (
          <>
            {error && (
              <div role="alert" style={banner("var(--danger)")}>
                {error}
              </div>
            )}
            {ok && <div style={banner("var(--success)")}>{ok}</div>}

            <Row>
              <Labelled label="Type">
                <input value={schema.type} disabled style={{ ...ctl, opacity: 0.7 }} />
              </Labelled>
              <Labelled label="Label">
                <input
                  value={schema.label}
                  onChange={(e) => setSchema({ ...schema, label: e.target.value })}
                  style={ctl}
                />
              </Labelled>
              <Labelled label="Naming pattern (regex on name)">
                <input
                  value={schema.naming_pattern ?? ""}
                  onChange={(e) =>
                    setSchema({ ...schema, naming_pattern: e.target.value || null })
                  }
                  placeholder="^[a-z][a-z0-9-]+$"
                  style={ctl}
                />
              </Labelled>
            </Row>

            <Labelled label="Required tags (comma-separated)">
              <input
                value={schema.required_tags.join(", ")}
                onChange={(e) =>
                  setSchema({
                    ...schema,
                    required_tags: e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                style={ctl}
              />
            </Labelled>

            <Section title="Fields">
              {schema.fields.map((f, i) => (
                <div key={i} style={rowGrid}>
                  <input
                    value={f.name}
                    placeholder="name"
                    onChange={(e) => patchField(i, { name: e.target.value })}
                    style={ctl}
                  />
                  <input
                    value={f.label}
                    placeholder="label"
                    onChange={(e) => patchField(i, { label: e.target.value })}
                    style={ctl}
                  />
                  <select
                    value={f.datatype}
                    onChange={(e) => patchField(i, { datatype: e.target.value })}
                    style={ctl}
                  >
                    {DATATYPES.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                  <input
                    value={(f.allowed_values ?? []).join(", ")}
                    placeholder="enum values"
                    onChange={(e) =>
                      patchField(i, {
                        allowed_values: e.target.value.trim()
                          ? e.target.value.split(",").map((s) => s.trim())
                          : null,
                      })
                    }
                    style={ctl}
                  />
                  <label style={chk}>
                    <input
                      type="checkbox"
                      checked={f.required}
                      onChange={(e) => patchField(i, { required: e.target.checked })}
                    />
                    req
                  </label>
                  <button onClick={() => setSchema({ ...schema, fields: schema.fields.filter((_, x) => x !== i) })} style={del}>
                    ✕
                  </button>
                </div>
              ))}
              <Button
                variant="ghost"
                onClick={() => setSchema({ ...schema, fields: [...schema.fields, emptyField()] })}
              >
                + Add field
              </Button>
            </Section>

            <Section title="Lineage (required relationships)">
              {lineage.relationships.map((r, i) => (
                <div key={i} style={relGrid}>
                  <input
                    value={r.name}
                    placeholder="relationship"
                    onChange={(e) => patchRel(i, { name: e.target.value })}
                    style={ctl}
                  />
                  <select
                    value={r.target_type}
                    onChange={(e) => patchRel(i, { target_type: e.target.value })}
                    style={ctl}
                  >
                    <option value="">— target type —</option>
                    {types.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                  <select value={r.direction} onChange={(e) => patchRel(i, { direction: e.target.value })} style={ctl}>
                    {DIRECTIONS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                  <select value={r.cardinality} onChange={(e) => patchRel(i, { cardinality: e.target.value })} style={ctl}>
                    {CARDINALITIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <label style={chk}>
                    <input
                      type="checkbox"
                      checked={r.required}
                      onChange={(e) => patchRel(i, { required: e.target.checked })}
                    />
                    req
                  </label>
                  <button
                    onClick={() =>
                      setLineage({ ...lineage, relationships: lineage.relationships.filter((_, x) => x !== i) })
                    }
                    style={del}
                  >
                    ✕
                  </button>
                </div>
              ))}
              <Button
                variant="ghost"
                onClick={() =>
                  setLineage({
                    ...lineage,
                    relationships: [
                      ...lineage.relationships,
                      { name: "", target_type: "", direction: "up", cardinality: "one", required: true },
                    ],
                  })
                }
              >
                + Add relationship
              </Button>
            </Section>

            <div style={{ marginTop: 16 }}>
              <Button onClick={save}>Validate &amp; save</Button>
            </div>
          </>
        ) : (
          <p style={{ color: "var(--text-muted)" }}>Select or create a CI type.</p>
        )}
      </main>
    </div>
  );
}

function banner(color: string): React.CSSProperties {
  return {
    padding: "8px 12px",
    borderRadius: 8,
    marginBottom: 12,
    fontSize: "0.82rem",
    color,
    border: `1px solid ${color}`,
    background: `color-mix(in srgb, ${color} 12%, transparent)`,
  };
}
const rowGrid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr 110px 1.2fr 56px 32px",
  gap: 6,
  marginBottom: 6,
  alignItems: "center",
};
const relGrid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr 90px 90px 56px 32px",
  gap: 6,
  marginBottom: 6,
  alignItems: "center",
};
const chk: React.CSSProperties = {
  display: "flex",
  gap: 4,
  alignItems: "center",
  fontSize: "0.72rem",
  color: "var(--text-muted)",
};
const del: React.CSSProperties = {
  border: "none",
  background: "transparent",
  color: "var(--text-muted)",
  cursor: "pointer",
};

function Row({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "flex", gap: 12, marginBottom: 10 }}>{children}</div>;
}
function Labelled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ flex: 1, display: "block" }}>
      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{label}</span>
      {children}
    </label>
  );
}
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginTop: 18 }}>
      <h2 style={{ fontSize: "0.95rem", margin: "0 0 8px" }}>{title}</h2>
      {children}
    </section>
  );
}

// Schema-driven node property panel. Renders guided controls from the backend NodeTypeSpec so
// every node type gets rich, typed parameters with no per-type UI code. Dynamic `source` fields
// (connectors, actions, CMDB tables/fields, workflows, roles) resolve their options at runtime.

import { useEffect, useState } from "react";
import {
  Connectors,
  type Capabilities,
  type CanvasNode,
  type CmdbField,
  type NodeFieldSpec,
  type NodeTypeSpec,
  type Workflow,
} from "@/shared/api/client";

const ROLES = ["admin", "engineer", "operator", "consumer"];

interface Option {
  value: string;
  label: string;
}

export function SchemaProperties(props: {
  node: CanvasNode;
  spec: NodeTypeSpec | undefined;
  caps: Capabilities[];
  workflows: Workflow[];
  onChange: (data: Record<string, unknown>) => void;
  onDelete: () => void;
}) {
  const { node, spec, caps, workflows, onChange, onDelete } = props;
  const data = node.data;
  const set = (k: string, v: unknown) => onChange({ ...data, [k]: v });

  // CMDB field catalogue — refetched when the chosen table changes (drives the field picker).
  const [cmdbTables, setCmdbTables] = useState<string[]>([]);
  const [cmdbFields, setCmdbFields] = useState<CmdbField[]>([]);
  const usesCmdb = spec?.fields.some((f) => f.source === "cmdb_fields" || f.source === "cmdb_tables");
  const table = String(data.table ?? "");
  useEffect(() => {
    if (!usesCmdb) return;
    Connectors.cmdbFields(table || undefined)
      .then((r) => {
        setCmdbTables(r.tables);
        setCmdbFields(r.fields);
      })
      .catch(() => undefined);
  }, [usesCmdb, table]);

  const execCaps = caps.filter((c) => c.category === "execution");
  const activeConn = execCaps.find((c) => c.kind === data.connector);

  function options(field: NodeFieldSpec): Option[] {
    if (field.choices) return field.choices.map((c) => ({ value: c, label: c }));
    switch (field.source) {
      case "execution_connectors":
        return execCaps.map((c) => ({ value: c.kind, label: c.display_name }));
      case "connector_actions":
        return (activeConn?.actions ?? []).map((a) => ({ value: a.name, label: a.label }));
      case "cmdb_tables":
        return cmdbTables.map((t) => ({ value: t, label: t }));
      case "cmdb_fields":
        return cmdbFields.map((f) => ({ value: f.name, label: `${f.label} (${f.name})` }));
      case "workflows":
        return workflows.map((w) => ({ value: w.id, label: w.name }));
      case "roles":
        return ROLES.map((r) => ({ value: r, label: r }));
      default:
        return [];
    }
  }

  if (!spec) {
    return <JsonArea label="Data (JSON)" value={data} onChange={onChange} />;
  }

  return (
    <div>
      <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", margin: "2px 0 12px" }}>
        {spec.description}
      </p>
      <label style={{ display: "block", margin: "10px 0" }}>
        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Name</span>
        <input value={String(data.name ?? "")} onChange={(e) => set("name", e.target.value)} style={ctl} />
      </label>
      {spec.fields.map((f) => (
        <FieldControl
          key={f.name}
          field={f}
          value={data[f.name]}
          options={options(f)}
          onChange={(v) => set(f.name, v)}
        />
      ))}
      <div style={{ marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
        <button
          onClick={onDelete}
          style={{
            width: "100%",
            padding: "7px",
            borderRadius: 7,
            border: "1px solid var(--color-danger)",
            background: "transparent",
            color: "var(--color-danger)",
            cursor: "pointer",
            fontSize: "0.8rem",
          }}
        >
          Delete node
        </button>
      </div>
    </div>
  );
}

function FieldControl({
  field,
  value,
  options,
  onChange,
}: {
  field: NodeFieldSpec;
  value: unknown;
  options: Option[];
  onChange: (v: unknown) => void;
}) {
  switch (field.type) {
    case "number":
      return (
        <Labeled field={field}>
          <input
            type="number"
            value={value === undefined || value === null ? "" : Number(value)}
            placeholder={field.placeholder}
            onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
            style={ctl}
          />
        </Labeled>
      );
    case "boolean":
      return (
        <label
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            margin: "10px 0",
            fontSize: "0.82rem",
          }}
        >
          <input type="checkbox" checked={!!value} onChange={(e) => onChange(e.target.checked)} />
          {field.label}
        </label>
      );
    case "select":
      return (
        <Labeled field={field}>
          <select value={String(value ?? "")} onChange={(e) => onChange(e.target.value)} style={ctl}>
            <option value="">—</option>
            {options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Labeled>
      );
    case "multiselect":
      return <MultiSelect field={field} value={asStrArray(value)} options={options} onChange={onChange} />;
    case "keyvalue":
      return <KeyValueEditor field={field} value={asRecord(value)} onChange={onChange} />;
    case "assignments":
      return <AssignmentsEditor field={field} value={asList(value)} onChange={onChange} />;
    case "cases":
      return <CasesEditor field={field} value={asList(value)} onChange={onChange} />;
    case "inputs":
      return <InputsEditor field={field} value={asList(value)} onChange={onChange} />;
    case "textarea":
    case "code":
      return (
        <Labeled field={field}>
          <textarea
            value={String(value ?? "")}
            placeholder={field.placeholder}
            onChange={(e) => onChange(e.target.value)}
            rows={4}
            style={{ ...ctl, fontFamily: field.type === "code" ? "ui-monospace, monospace" : "inherit" }}
          />
        </Labeled>
      );
    default:
      return (
        <Labeled field={field}>
          <input
            value={String(value ?? "")}
            placeholder={field.placeholder}
            onChange={(e) => onChange(e.target.value)}
            style={ctl}
          />
        </Labeled>
      );
  }
}

// --- composite editors ----------------------------------------------------------------------

function MultiSelect({
  field,
  value,
  options,
  onChange,
}: {
  field: NodeFieldSpec;
  value: string[];
  options: Option[];
  onChange: (v: string[]) => void;
}) {
  const toggle = (v: string) =>
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  return (
    <Labeled field={field}>
      <div
        style={{
          border: "1px solid var(--border)",
          borderRadius: 7,
          padding: 8,
          maxHeight: 168,
          overflow: "auto",
          background: "var(--bg)",
        }}
      >
        {options.length === 0 && (
          <span style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>No options</span>
        )}
        {options.map((o) => (
          <label
            key={o.value}
            style={{ display: "flex", gap: 7, alignItems: "center", fontSize: "0.78rem", padding: "2px 0" }}
          >
            <input
              type="checkbox"
              checked={value.includes(o.value)}
              onChange={() => toggle(o.value)}
            />
            {o.label}
          </label>
        ))}
      </div>
    </Labeled>
  );
}

function KeyValueEditor({
  field,
  value,
  onChange,
}: {
  field: NodeFieldSpec;
  value: Record<string, unknown>;
  onChange: (v: Record<string, unknown>) => void;
}) {
  const entries = Object.entries(value);
  const setKey = (i: number, k: string) => {
    const next: Record<string, unknown> = {};
    entries.forEach(([ek, ev], idx) => {
      next[idx === i ? k : ek] = ev;
    });
    onChange(next);
  };
  const setVal = (k: string, v: string) => onChange({ ...value, [k]: v });
  const remove = (k: string) => {
    const next = { ...value };
    delete next[k];
    onChange(next);
  };
  return (
    <Labeled field={field}>
      {entries.map(([k, v], i) => (
        <div key={i} style={{ display: "flex", gap: 4, marginBottom: 4 }}>
          <input value={k} onChange={(e) => setKey(i, e.target.value)} placeholder="key" style={{ ...ctl, marginTop: 0 }} />
          <input value={String(v ?? "")} onChange={(e) => setVal(k, e.target.value)} placeholder="value" style={{ ...ctl, marginTop: 0 }} />
          <RemoveBtn onClick={() => remove(k)} />
        </div>
      ))}
      <AddBtn label="+ Add row" onClick={() => onChange({ ...value, "": "" })} />
    </Labeled>
  );
}

function AssignmentsEditor({
  field,
  value,
  onChange,
}: {
  field: NodeFieldSpec;
  value: Record<string, unknown>[];
  onChange: (v: Record<string, unknown>[]) => void;
}) {
  const upd = (i: number, patch: Record<string, unknown>) =>
    onChange(value.map((row, idx) => (idx === i ? { ...row, ...patch } : row)));
  return (
    <Labeled field={field}>
      {value.map((row, i) => (
        <div key={i} style={{ display: "flex", gap: 4, marginBottom: 4 }}>
          <input value={String(row.key ?? "")} onChange={(e) => upd(i, { key: e.target.value })} placeholder="variable" style={{ ...ctl, marginTop: 0 }} />
          <input value={String(row.value ?? "")} onChange={(e) => upd(i, { value: e.target.value })} placeholder="{{expression}}" style={{ ...ctl, marginTop: 0 }} />
          <RemoveBtn onClick={() => onChange(value.filter((_, idx) => idx !== i))} />
        </div>
      ))}
      <AddBtn label="+ Add assignment" onClick={() => onChange([...value, { key: "", value: "" }])} />
    </Labeled>
  );
}

function CasesEditor({
  field,
  value,
  onChange,
}: {
  field: NodeFieldSpec;
  value: Record<string, unknown>[];
  onChange: (v: Record<string, unknown>[]) => void;
}) {
  const upd = (i: number, patch: Record<string, unknown>) =>
    onChange(value.map((row, idx) => (idx === i ? { ...row, ...patch } : row)));
  return (
    <Labeled field={field}>
      {value.map((row, i) => (
        <div key={i} style={{ display: "flex", gap: 4, marginBottom: 4 }}>
          <input value={String(row.value ?? "")} onChange={(e) => upd(i, { value: e.target.value })} placeholder="when value" style={{ ...ctl, marginTop: 0 }} />
          <input value={String(row.handle ?? "")} onChange={(e) => upd(i, { handle: e.target.value })} placeholder="→ handle" style={{ ...ctl, marginTop: 0 }} />
          <RemoveBtn onClick={() => onChange(value.filter((_, idx) => idx !== i))} />
        </div>
      ))}
      <AddBtn label="+ Add case" onClick={() => onChange([...value, { value: "", handle: "" }])} />
    </Labeled>
  );
}

function InputsEditor({
  field,
  value,
  onChange,
}: {
  field: NodeFieldSpec;
  value: Record<string, unknown>[];
  onChange: (v: Record<string, unknown>[]) => void;
}) {
  const upd = (i: number, patch: Record<string, unknown>) =>
    onChange(value.map((row, idx) => (idx === i ? { ...row, ...patch } : row)));
  return (
    <Labeled field={field}>
      {value.map((row, i) => (
        <div key={i} style={{ display: "flex", gap: 4, marginBottom: 4 }}>
          <input value={String(row.name ?? "")} onChange={(e) => upd(i, { name: e.target.value })} placeholder="name" style={{ ...ctl, marginTop: 0 }} />
          <select value={String(row.type ?? "string")} onChange={(e) => upd(i, { type: e.target.value })} style={{ ...ctl, marginTop: 0, flex: "0 0 84px" }}>
            {["string", "number", "boolean"].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input value={String(row.default ?? "")} onChange={(e) => upd(i, { default: e.target.value })} placeholder="default" style={{ ...ctl, marginTop: 0 }} />
          <RemoveBtn onClick={() => onChange(value.filter((_, idx) => idx !== i))} />
        </div>
      ))}
      <AddBtn label="+ Add input" onClick={() => onChange([...value, { name: "", type: "string", default: "" }])} />
    </Labeled>
  );
}

// --- small shared pieces ---------------------------------------------------------------------

function Labeled({ field, children }: { field: NodeFieldSpec; children: React.ReactNode }) {
  return (
    <label style={{ display: "block", margin: "10px 0" }}>
      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
        {field.label}
        {field.required && <span style={{ color: "var(--color-danger)" }}> *</span>}
      </span>
      {children}
      {field.help && (
        <span style={{ display: "block", fontSize: "0.68rem", color: "var(--text-muted)", marginTop: 2 }}>
          {field.help}
        </span>
      )}
    </label>
  );
}

function AddBtn({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontSize: "0.72rem",
        padding: "4px 8px",
        borderRadius: 6,
        border: "1px dashed var(--border)",
        background: "transparent",
        color: "var(--text-muted)",
        cursor: "pointer",
      }}
    >
      {label}
    </button>
  );
}

function RemoveBtn({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      title="Remove"
      style={{
        flex: "0 0 26px",
        borderRadius: 6,
        border: "1px solid var(--border)",
        background: "transparent",
        color: "var(--text-muted)",
        cursor: "pointer",
      }}
    >
      ×
    </button>
  );
}

function JsonArea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: unknown;
  onChange: (v: Record<string, unknown>) => void;
}) {
  const [text, setText] = useState(JSON.stringify(value, null, 2));
  const [err, setErr] = useState(false);
  return (
    <label style={{ display: "block", margin: "10px 0" }}>
      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{label}</span>
      <textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          try {
            onChange(JSON.parse(e.target.value));
            setErr(false);
          } catch {
            setErr(true);
          }
        }}
        rows={8}
        style={{
          ...ctl,
          fontFamily: "ui-monospace, monospace",
          fontSize: "0.75rem",
          borderColor: err ? "var(--color-danger)" : "var(--border)",
        }}
      />
    </label>
  );
}

function asStrArray(v: unknown): string[] {
  return Array.isArray(v) ? v.map(String) : [];
}
function asRecord(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
}
function asList(v: unknown): Record<string, unknown>[] {
  return Array.isArray(v) ? (v as Record<string, unknown>[]) : [];
}

const ctl: React.CSSProperties = {
  width: "100%",
  marginTop: 4,
  padding: "7px 9px",
  borderRadius: 7,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
  boxSizing: "border-box",
};

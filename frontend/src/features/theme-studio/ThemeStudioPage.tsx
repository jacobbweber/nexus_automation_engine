// Theme Studio (B13): a fully deterministic theme authoring surface — pick a starting theme, edit
// tokens with color pickers, see a live kitchen-sink preview + validation, and save to the server
// (which re-validates). No AI anywhere (ADR-0008); validateTheme is the gate.

import { useMemo, useRef, useState, type CSSProperties } from "react";
import { Themes, type ServerThemeDoc } from "@/shared/api/client";
import { Button, Card, Page, StatusBadge } from "@/shared/ui/primitives";
import { useTheme } from "@/shared/theme/theme-provider";
import { BASE_DARK, BASE_LIGHT, type Tokens } from "@/shared/theme/themes/base";
import { THEME_SCHEMA, nudgeForContrast, validateTheme } from "@/shared/theme/theme-schema";

const GROUPS: { label: string; keys: string[] }[] = [
  { label: "Surfaces", keys: ["--bg", "--surface", "--surface-2", "--surface-3"] },
  { label: "Text", keys: ["--text", "--text-muted", "--text-subtle"] },
  { label: "Lines", keys: ["--border", "--border-strong"] },
  { label: "Accent", keys: ["--accent", "--accent-hover", "--accent-contrast"] },
  { label: "Status", keys: ["--success", "--warn", "--danger", "--info"] },
  { label: "Run status", keys: ["--run-running", "--run-ok", "--run-warn", "--run-failed", "--run-skipped"] },
  { label: "System", keys: ["--focus", "--link"] },
];

const RUN_STATUSES = ["running", "completed", "failed", "pending", "skipped"];

export function ThemeStudioPage() {
  const { themes, builtinIds, reload } = useTheme();
  const fileRef = useRef<HTMLInputElement>(null);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const [id, setId] = useState("my-theme");
  const [name, setName] = useState("My Theme");
  const [base, setBase] = useState<"light" | "dark">("light");
  const [light, setLight] = useState<Tokens>({ ...BASE_LIGHT });
  const [dark, setDark] = useState<Tokens>({ ...BASE_DARK });
  const [editMode, setEditMode] = useState<"light" | "dark">("light");
  const [saved, setSaved] = useState<string | null>(null);

  const doc: ServerThemeDoc = useMemo(
    () => ({ $schema: THEME_SCHEMA, id, name, base, tokens: { light, dark } }),
    [id, name, base, light, dark],
  );
  const result = useMemo(() => validateTheme(doc), [doc]);

  const tokens = editMode === "light" ? light : dark;
  const setToken = (k: string, v: string) =>
    (editMode === "light" ? setLight : setDark)((t) => ({ ...t, [k]: v }));

  function startFrom(themeId: string) {
    const t = themes.find((x) => x.id === themeId);
    if (!t) return;
    setLight({ ...BASE_LIGHT, ...t.tokens.light });
    setDark({ ...BASE_DARK, ...t.tokens.dark });
  }

  function autoFixContrast() {
    const fix = (t: Tokens): Tokens => {
      const n = { ...t };
      n["--text"] = nudgeForContrast(n["--text"], n["--bg"]);
      n["--text-muted"] = nudgeForContrast(n["--text-muted"], n["--bg"]);
      n["--accent-contrast"] = nudgeForContrast(n["--accent-contrast"], n["--accent"]);
      return n;
    };
    setLight(fix);
    setDark(fix);
  }

  async function save() {
    setSaved(null);
    try {
      await Themes.save(doc);
      reload();
      setSaved("Saved — available in the theme picker.");
    } catch (e) {
      setSaved(e instanceof Error ? `Save failed: ${e.message}` : "Save failed");
    }
  }

  function exportTheme() {
    const blob = new Blob([JSON.stringify(doc, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${id || "theme"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function importFile(file: File) {
    setImportMsg(null);
    try {
      const parsed = JSON.parse(await file.text());
      const r = validateTheme(parsed);
      if (!r.ok) {
        setImportMsg(`Invalid theme: ${r.errors[0] ?? "failed validation"}`);
        return;
      }
      setId(String(parsed.id ?? "imported"));
      setName(String(parsed.name ?? "Imported"));
      setBase(parsed.base === "dark" ? "dark" : "light");
      setLight({ ...BASE_LIGHT, ...parsed.tokens.light });
      setDark({ ...BASE_DARK, ...parsed.tokens.dark });
      setImportMsg("Imported into the editor — preview, then Save.");
    } catch {
      setImportMsg("Could not read that file (expected theme JSON).");
    }
  }

  async function removeTheme(themeId: string) {
    await Themes.remove(themeId).catch(() => undefined);
    reload();
  }

  const customThemes = themes.filter((t) => !builtinIds.has(t.id));

  // Preview wrapper: apply the edited mode's tokens directly as CSS variables on a scoped subtree.
  const previewStyle = { ...tokens, background: "var(--bg)", color: "var(--text)" } as CSSProperties;

  return (
    <Page title="Theme Studio" subtitle="Author a theme — deterministic, accessibility-validated, no AI">
      <div style={{ display: "grid", gridTemplateColumns: "minmax(320px, 420px) 1fr", gap: 16, alignItems: "start" }}>
        {/* ---- editor ---- */}
        <Card>
          <div style={{ display: "grid", gap: 10 }}>
            <Row>
              <Labeled label="Name"><input value={name} onChange={(e) => setName(e.target.value)} style={ctl} /></Labeled>
              <Labeled label="Id"><input value={id} onChange={(e) => setId(e.target.value)} style={ctl} /></Labeled>
            </Row>
            <Row>
              <Labeled label="Default mode">
                <select value={base} onChange={(e) => setBase(e.target.value as "light" | "dark")} style={ctl}>
                  <option value="light">light</option>
                  <option value="dark">dark</option>
                </select>
              </Labeled>
              <Labeled label="Start from">
                <select defaultValue="" onChange={(e) => e.target.value && startFrom(e.target.value)} style={ctl}>
                  <option value="">— theme —</option>
                  {themes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </Labeled>
            </Row>

            <div role="radiogroup" aria-label="Editing mode" style={{ display: "flex", gap: 4 }}>
              {(["light", "dark"] as const).map((m) => (
                <button key={m} role="radio" aria-checked={editMode === m} onClick={() => setEditMode(m)}
                  style={{ flex: 1, padding: "6px", borderRadius: "var(--radius-sm)", cursor: "pointer", textTransform: "capitalize",
                    border: "1px solid var(--border)", fontSize: "0.78rem",
                    background: editMode === m ? "var(--accent)" : "transparent",
                    color: editMode === m ? "var(--accent-contrast)" : "var(--text-muted)" }}>
                  Editing: {m}
                </button>
              ))}
            </div>

            {GROUPS.map((g) => (
              <div key={g.label}>
                <div style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", margin: "6px 0 4px" }}>{g.label}</div>
                {g.keys.map((k) => (
                  <div key={k} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <input type="color" value={tokens[k] ?? "#000000"} onChange={(e) => setToken(k, e.target.value)}
                      style={{ width: 32, height: 28, border: "1px solid var(--border)", borderRadius: 6, background: "none" }} aria-label={k} />
                    <code style={{ fontSize: "0.72rem", flex: 1, color: "var(--text-muted)" }}>{k}</code>
                    <input value={tokens[k] ?? ""} onChange={(e) => setToken(k, e.target.value)} style={{ ...ctl, width: 96, fontFamily: "var(--font-mono)" }} />
                  </div>
                ))}
              </div>
            ))}

            <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
              <Button onClick={save} disabled={!result.ok}>Save theme</Button>
              <Button variant="ghost" onClick={autoFixContrast}>Auto-fix contrast</Button>
            </div>
            {saved && <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{saved}</p>}
          </div>
        </Card>

        {/* ---- validation + live preview ---- */}
        <div style={{ display: "grid", gap: 16 }}>
          <Card>
            <SectionTitle>Validation {result.ok ? "— passes" : "— fix to save"}</SectionTitle>
            {result.errors.length === 0 && <p style={{ color: "var(--success)", fontSize: "0.82rem" }}>Meets the contract + WCAG AA.</p>}
            {result.errors.map((e, i) => (
              <p key={i} style={{ color: "var(--danger)", fontSize: "0.78rem", margin: "2px 0" }}>• {e}</p>
            ))}
            {result.warnings.map((w, i) => (
              <p key={i} style={{ color: "var(--warn)", fontSize: "0.78rem", margin: "2px 0" }}>• {w}</p>
            ))}
          </Card>

          <Card style={{ padding: 0, overflow: "hidden" }}>
            <SectionTitle style={{ padding: "14px 16px 0" }}>Live preview — {editMode}</SectionTitle>
            <div style={{ ...previewStyle, padding: 16, margin: 12, borderRadius: "var(--radius-lg)", border: "1px solid var(--border)" }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
                <Btn bg="var(--accent)" fg="var(--accent-contrast)">Primary</Btn>
                <Btn bg="var(--accent-soft)" fg="var(--accent)">Soft</Btn>
                <Btn bg="transparent" fg="var(--text)" border>Ghost</Btn>
                <Btn bg="var(--danger)" fg="#fff">Danger</Btn>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
                {RUN_STATUSES.map((s) => <StatusBadge key={s} status={s} />)}
              </div>
              <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: 12 }}>
                <div style={{ fontWeight: 600 }}>Card heading</div>
                <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", margin: "4px 0 0" }}>
                  Muted body text on a surface, with a <span style={{ color: "var(--link)" }}>link</span>.
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <SectionTitle>Library &amp; portability</SectionTitle>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
              <Button variant="ghost" onClick={exportTheme}>Export draft (JSON)</Button>
              <Button variant="ghost" onClick={() => fileRef.current?.click()}>Import theme…</Button>
              <input
                ref={fileRef}
                type="file"
                accept="application/json,.json"
                style={{ display: "none" }}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void importFile(f);
                  e.target.value = "";
                }}
              />
            </div>
            {importMsg && <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "0 0 8px" }}>{importMsg}</p>}
            <div style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 4 }}>
              Custom themes
            </div>
            {customThemes.length === 0 && (
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>None yet — save or import one above.</p>
            )}
            {customThemes.map((t) => (
              <div key={t.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "5px 0", borderTop: "1px solid var(--border)" }}>
                <span style={{ fontSize: "0.82rem" }}>{t.name} <code style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>{t.id}</code></span>
                <Button size="sm" variant="ghost" onClick={() => removeTheme(t.id)}>Delete</Button>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </Page>
  );
}

function Btn({ bg, fg, border, children }: { bg: string; fg: string; border?: boolean; children: React.ReactNode }) {
  return (
    <span style={{ background: bg, color: fg, padding: "8px 14px", borderRadius: "var(--radius-md)", fontSize: "0.82rem", fontWeight: 600,
      border: border ? "1px solid var(--border)" : "1px solid transparent" }}>{children}</span>
  );
}
function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return <label style={{ display: "grid", gap: 3, flex: 1 }}><span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{label}</span>{children}</label>;
}
function Row({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "flex", gap: 8 }}>{children}</div>;
}
function SectionTitle({ children, style }: { children: React.ReactNode; style?: CSSProperties }) {
  return <h2 style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0, ...style }}>{children}</h2>;
}

const ctl: CSSProperties = {
  width: "100%", padding: "7px 9px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)",
  background: "var(--bg)", color: "var(--text)", boxSizing: "border-box", fontSize: "0.8rem",
};

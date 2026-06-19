import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Catalog, type CatalogFacets, type Template } from "@/shared/api/client";
import { Button, Card, Page } from "@/shared/ui/primitives";
import { AutomationDetail } from "./AutomationDetail";
import { CompareTemplates } from "./CompareTemplates";

const RISK_COLOR: Record<string, string> = {
  low: "var(--color-ok)",
  medium: "var(--color-warn)",
  high: "var(--color-danger)",
  critical: "#b5402f",
};

export function CatalogPage() {
  const [facets, setFacets] = useState<CatalogFacets>({ domain: {}, vendor: {} });
  const [templates, setTemplates] = useState<Template[]>([]);
  const [domain, setDomain] = useState<string>("");
  const [vendor, setVendor] = useState<string>("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Template | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [comparing, setComparing] = useState(false);

  const toggleCompare = (id: string) =>
    setCompareIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : ids.length < 3 ? [...ids, id] : ids));
  const compareTemplates = templates.filter((t) => compareIds.includes(t.id));

  useEffect(() => {
    Catalog.facets().then(setFacets).catch(() => undefined);
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      Catalog.list({ domain, vendor, search }).then(setTemplates).catch(() => setTemplates([]));
    }, 150);
    return () => clearTimeout(t);
  }, [domain, vendor, search]);

  const grouped = useMemo(() => {
    const by: Record<string, Template[]> = {};
    for (const t of templates) (by[t.domain] ??= []).push(t);
    return Object.entries(by).sort((a, b) => a[0].localeCompare(b[0]));
  }, [templates]);

  return (
    <Page title="Service Catalog" subtitle={`${templates.length} automations across all engines`}>
      <div style={{ display: "grid", gridTemplateColumns: "210px 1fr", gap: 18 }}>
        {/* Facet rail */}
        <div>
          <SearchBox value={search} onChange={setSearch} />
          <Facet title="Domain" active={domain} counts={facets.domain} onPick={setDomain} />
          <Facet title="Vendor" active={vendor} counts={facets.vendor} onPick={setVendor} />
        </div>

        {/* Results, grouped by domain */}
        <div>
          {grouped.map(([dom, items]) => (
            <div key={dom} style={{ marginBottom: 22 }}>
              <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)" }}>
                {dom} <span style={{ opacity: 0.6 }}>· {items.length}</span>
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: 12 }}>
                {items.map((t) => (
                  <button key={t.id} onClick={() => setSelected(t)} style={cardBtn}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "0.66rem", textTransform: "uppercase", color: "var(--color-accent)" }}>
                        {t.vendor || t.connector}
                      </span>
                      <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <label
                          onClick={(e) => e.stopPropagation()}
                          title="Add to compare"
                          style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.62rem", color: "var(--text-muted)" }}
                        >
                          <input
                            type="checkbox"
                            checked={compareIds.includes(t.id)}
                            onChange={() => toggleCompare(t.id)}
                            aria-label={`Compare ${t.name}`}
                          />
                          compare
                        </label>
                        <RiskPill risk={t.risk} />
                      </span>
                    </div>
                    <div style={{ fontWeight: 600, margin: "6px 0 4px" }}>{t.name}</div>
                    <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", minHeight: 34, lineHeight: 1.35 }}>
                      {t.description}
                    </div>
                    <div style={{ display: "flex", gap: 8, marginTop: 8, fontSize: "0.68rem", color: "var(--text-muted)" }}>
                      <span>{t.atomic ? "Atomic" : "Orchestrated"}</span>
                      <span>· ~{t.estimated_minutes}m</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
          {templates.length === 0 && (
            <Card><span style={{ color: "var(--text-muted)" }}>No automations match.</span></Card>
          )}
        </div>
      </div>
      {selected && <AutomationDetail template={selected} onClose={() => setSelected(null)} />}

      {compareIds.length > 0 && (
        <div
          style={{
            position: "fixed",
            bottom: 18,
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "10px 16px",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-pill)",
            boxShadow: "var(--shadow-3)",
            zIndex: 900,
          }}
        >
          <span style={{ fontSize: "0.82rem" }}>{compareIds.length} selected to compare</span>
          <Button size="sm" onClick={() => setComparing(true)} disabled={compareIds.length < 2}>
            Compare
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setCompareIds([])}>
            Clear
          </Button>
        </div>
      )}
      {comparing && <CompareTemplates templates={compareTemplates} onClose={() => setComparing(false)} />}
    </Page>
  );
}

function SearchBox({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ position: "relative", marginBottom: 16 }}>
      <Search size={15} style={{ position: "absolute", left: 9, top: 9, color: "var(--text-muted)" }} />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search automations…"
        style={{ width: "100%", padding: "7px 9px 7px 30px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
      />
    </div>
  );
}

function Facet({ title, active, counts, onPick }: {
  title: string;
  active: string;
  counts: Record<string, number>;
  onPick: (v: string) => void;
}) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ fontSize: "0.7rem", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 6 }}>{title}</div>
      <FacetItem label="All" active={active === ""} onClick={() => onPick("")} />
      {entries.map(([k, n]) => (
        <FacetItem key={k} label={k} count={n} active={active === k} onClick={() => onPick(active === k ? "" : k)} />
      ))}
    </div>
  );
}

function FacetItem({ label, count, active, onClick }: { label: string; count?: number; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      display: "flex", justifyContent: "space-between", width: "100%", padding: "5px 8px",
      borderRadius: 6, border: "none", cursor: "pointer", fontSize: "0.82rem", marginBottom: 2,
      background: active ? "var(--surface-2)" : "transparent",
      color: active ? "var(--text)" : "var(--text-muted)",
    }}>
      <span>{label}</span>
      {count !== undefined && <span style={{ opacity: 0.6 }}>{count}</span>}
    </button>
  );
}

function RiskPill({ risk }: { risk: string }) {
  return (
    <span style={{ fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase", color: RISK_COLOR[risk] ?? "var(--text-muted)" }}>
      {risk}
    </span>
  );
}

const cardBtn: React.CSSProperties = {
  textAlign: "left",
  border: "1px solid var(--border)",
  borderRadius: 12,
  background: "var(--surface)",
  padding: 14,
  cursor: "pointer",
  color: "var(--text)",
};

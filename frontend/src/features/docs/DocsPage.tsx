// In-app documentation (M29.4) — renders the authored docs/ tree (served by the backend so it stays
// the single source of truth) with a searchable sidebar + the live generated reference.

import { useCallback, useEffect, useMemo, useState } from "react";
import { Docs, type DocPage } from "@/shared/api/client";
import { Markdown } from "@/shared/ui/Markdown";

export function DocsPage() {
  const [pages, setPages] = useState<DocPage[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    Docs.pages()
      .then((p) => {
        setPages(p);
        if (p.length) setActive(p.find((x) => x.path === "README.md")?.path ?? p[0].path);
      })
      .catch(() => setPages([]));
  }, []);

  const open = useCallback((path: string) => {
    setActive(path);
    if (path === "__reference__") {
      Docs.reference()
        .then((ref) => setContent("```json\n" + JSON.stringify(ref, null, 2) + "\n```"))
        .catch(() => setContent("_Reference unavailable._"));
      return;
    }
    Docs.page(path).then((d) => setContent(d.content)).catch(() => setContent("_Not found._"));
  }, []);

  useEffect(() => {
    if (active && active !== "__reference__") open(active);
  }, [active, open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? pages.filter((p) => p.title.toLowerCase().includes(q) || p.path.toLowerCase().includes(q)) : pages;
  }, [pages, query]);

  return (
    <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
      <aside style={{ width: 240, flexShrink: 0 }}>
        <h1 style={{ fontSize: "1.1rem", margin: "0 0 8px" }}>Documentation</h1>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search docs…"
          style={{
            width: "100%", padding: "7px 10px", borderRadius: 8, marginBottom: 10,
            border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)",
            boxSizing: "border-box",
          }}
        />
        <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {filtered.map((p) => (
            <button
              key={p.path}
              onClick={() => setActive(p.path)}
              style={navBtn(active === p.path)}
              title={p.path}
            >
              {p.title}
            </button>
          ))}
          <button
            onClick={() => {
              setActive("__reference__");
              open("__reference__");
            }}
            style={{ ...navBtn(active === "__reference__"), marginTop: 8, fontStyle: "italic" }}
          >
            Reference (generated)
          </button>
        </nav>
      </aside>
      <main style={{ flex: 1, minWidth: 0 }}>
        <Markdown source={content} />
      </main>
    </div>
  );
}

function navBtn(activeState: boolean): React.CSSProperties {
  return {
    textAlign: "left",
    padding: "6px 10px",
    borderRadius: 8,
    border: "none",
    cursor: "pointer",
    fontSize: "0.84rem",
    background: activeState ? "var(--accent-soft)" : "transparent",
    color: "var(--text)",
  };
}

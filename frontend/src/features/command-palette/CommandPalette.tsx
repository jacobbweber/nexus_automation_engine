// Global ⌘K / Ctrl-K command palette — fuzzy "find-and-run anything": jump to any area, open a
// saved workflow, or run a quick action. Keyboard-first; recents persisted.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Canvas, type Workflow } from "@/shared/api/client";
import { rank } from "./fuzzy";

interface Command {
  id: string;
  label: string;
  group: string;
  keywords?: string;
  run: () => void;
}

const RECENTS_KEY = "nexus_cmd_recents";

function loadRecents(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENTS_KEY) || "[]");
  } catch {
    return [];
  }
}

export function CommandPalette() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [recents, setRecents] = useState<string[]>(loadRecents);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global hotkey.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Load workflows when first opened.
  useEffect(() => {
    if (open && workflows.length === 0) Canvas.list().then(setWorkflows).catch(() => undefined);
  }, [open, workflows.length]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelected(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const commands = useMemo<Command[]>(() => {
    const go = (to: string) => () => {
      navigate(to);
      setOpen(false);
    };
    const nav: Command[] = [
      { id: "go:dashboard", label: "Dashboard", group: "Go to", keywords: "home overview", run: go("/") },
      { id: "go:catalog", label: "Catalog", group: "Go to", keywords: "automations templates", run: go("/catalog") },
      { id: "go:canvas", label: "Canvas", group: "Go to", keywords: "workflow builder", run: go("/canvas") },
      { id: "go:library", label: "Library", group: "Go to", keywords: "saved workflows reporting", run: go("/library") },
      { id: "go:console", label: "Console", group: "Go to", keywords: "runs logs jobs", run: go("/console") },
      { id: "go:incidents", label: "Incidents", group: "Go to", keywords: "failures kanban", run: go("/incidents") },
      { id: "go:governance", label: "Governance", group: "Go to", keywords: "approvals change review", run: go("/governance") },
      { id: "go:admin", label: "Admin", group: "Go to", keywords: "rbac users", run: go("/admin") },
    ];
    const actions: Command[] = [
      { id: "act:new-workflow", label: "New workflow", group: "Actions", keywords: "create canvas", run: go("/canvas") },
      { id: "act:theme-studio", label: "Open Theme Studio", group: "Actions", keywords: "theme appearance", run: go("/theme-studio") },
      { id: "act:accessibility", label: "Open Accessibility Center", group: "Actions", keywords: "a11y mode dark light density contrast dyslexia text size", run: go("/accessibility") },
      { id: "act:cmdb-schema", label: "Open CMDB Schema Studio", group: "Actions", keywords: "cmdb ci type schema lineage health configuration item", run: go("/cmdb-schema") },
      { id: "act:cmdb-explorer", label: "Open CMDB Lineage Explorer", group: "Actions", keywords: "cmdb ci health lineage explorer score gaps configuration item", run: go("/cmdb-explorer") },
      { id: "act:compliance", label: "Open Compliance posture", group: "Actions", keywords: "compliance drift posture desired observed reconcile sweep", run: go("/compliance") },
      { id: "act:approvals", label: "Open Approvals queue", group: "Actions", keywords: "review approval packet executive technical approve reject pending", run: go("/approvals") },
      { id: "act:determinism", label: "Open Determinism & Guardrails", group: "Actions", keywords: "pinning rules guarantee coverage drift enforce assert gate guardrails determinism", run: go("/determinism") },
      { id: "act:gitops", label: "Open GitOps (config as code)", group: "Actions", keywords: "gitops git config backup version history diff restore commit", run: go("/gitops") },
    ];
    const wf: Command[] = workflows.map((w) => ({
      id: `wf:${w.id}`,
      label: w.name,
      group: "Workflows",
      keywords: `${w.team ?? ""} ${(w.tags ?? []).join(" ")}`,
      run: () => {
        navigate(`/canvas?id=${w.id}`);
        setOpen(false);
      },
    }));
    return [...nav, ...actions, ...wf];
  }, [navigate, workflows]);

  const results = useMemo(() => {
    if (!query.trim()) {
      const recentCmds = recents
        .map((id) => commands.find((c) => c.id === id))
        .filter((c): c is Command => !!c);
      const rest = commands.filter((c) => !recents.includes(c.id));
      return [...recentCmds, ...rest].slice(0, 50);
    }
    return rank(commands, query).slice(0, 50);
  }, [commands, query, recents]);

  const runCommand = useCallback(
    (cmd: Command) => {
      const next = [cmd.id, ...recents.filter((r) => r !== cmd.id)].slice(0, 6);
      setRecents(next);
      try {
        localStorage.setItem(RECENTS_KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      cmd.run();
    },
    [recents],
  );

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelected((s) => Math.min(results.length - 1, s + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelected((s) => Math.max(0, s - 1));
    } else if (e.key === "Enter" && results[selected]) {
      e.preventDefault();
      runCommand(results[selected]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  if (!open) return null;

  return (
    <div
      onClick={() => setOpen(false)}
      style={{ position: "fixed", inset: 0, background: "var(--overlay)", display: "grid", placeItems: "start center", paddingTop: "12vh", zIndex: 1000 }}
    >
      <div
        role="dialog"
        aria-label="Command palette"
        onClick={(e) => e.stopPropagation()}
        style={{ width: "min(620px, 92vw)", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", boxShadow: "var(--shadow-3)", overflow: "hidden" }}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelected(0);
          }}
          onKeyDown={onKeyDown}
          placeholder="Search areas, workflows, actions…"
          aria-label="Search commands"
          style={{ width: "100%", padding: "16px 18px", border: "none", borderBottom: "1px solid var(--border)", background: "transparent", color: "var(--text)", fontSize: "1rem", outline: "none", boxSizing: "border-box" }}
        />
        <div style={{ maxHeight: "50vh", overflow: "auto", padding: 6 }}>
          {results.length === 0 && (
            <div style={{ padding: "16px 14px", color: "var(--text-muted)", fontSize: "0.85rem" }}>No matches.</div>
          )}
          {results.map((cmd, i) => (
            <button
              key={cmd.id}
              onMouseEnter={() => setSelected(i)}
              onClick={() => runCommand(cmd)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                width: "100%",
                textAlign: "left",
                padding: "9px 12px",
                borderRadius: "var(--radius-md)",
                border: "none",
                cursor: "pointer",
                background: i === selected ? "var(--accent-soft)" : "transparent",
                color: "var(--text)",
              }}
            >
              <span style={{ flex: 1, fontSize: "0.88rem" }}>{cmd.label}</span>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{cmd.group}</span>
            </button>
          ))}
        </div>
        <div style={{ padding: "8px 14px", borderTop: "1px solid var(--border)", fontSize: "0.7rem", color: "var(--text-muted)", display: "flex", gap: 14 }}>
          <span>↑↓ navigate</span>
          <span>↵ run</span>
          <span>esc close</span>
          <span style={{ marginLeft: "auto" }}>⌘K / Ctrl-K</span>
        </div>
      </div>
    </div>
  );
}

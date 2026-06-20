// Pure graph linter for the canvas (F27): catches structural problems before a run — missing
// start/end, dangling edges, unreachable nodes, cycles, and missing required parameters (per the
// node-type schema). Surfaced inline so operators fix issues before executing.

import type { CanvasEdge, CanvasNode, NodeTypeSpec } from "@/shared/api/client";

export interface LintIssue {
  severity: "error" | "warn";
  nodeId?: string;
  message: string;
}

function isEmpty(v: unknown): boolean {
  return v === undefined || v === null || v === "" ||
    (Array.isArray(v) && v.length === 0) ||
    (typeof v === "object" && !Array.isArray(v) && Object.keys(v as object).length === 0);
}

export function lintGraph(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  specs: NodeTypeSpec[],
): LintIssue[] {
  const issues: LintIssue[] = [];
  const ids = new Set(nodes.map((n) => n.id));
  const specByType = new Map(specs.map((s) => [s.type, s]));

  const starts = nodes.filter((n) => n.type === "start");
  if (nodes.length > 0 && starts.length === 0) issues.push({ severity: "error", message: "No Start node." });
  if (starts.length > 1) issues.push({ severity: "warn", message: "More than one Start node." });
  if (nodes.length > 0 && !nodes.some((n) => n.type === "end"))
    issues.push({ severity: "warn", message: "No End node — outputs won't be compiled." });

  // dangling edges
  for (const e of edges) {
    if (!ids.has(e.source) || !ids.has(e.target))
      issues.push({ severity: "error", message: `Edge references a missing node (${e.source}→${e.target}).` });
  }

  // adjacency over valid edges
  const adj = new Map<string, string[]>();
  for (const e of edges) {
    if (ids.has(e.source) && ids.has(e.target)) (adj.get(e.source) ?? adj.set(e.source, []).get(e.source)!).push(e.target);
  }

  // reachability from start(s)
  if (starts.length > 0) {
    const seen = new Set<string>();
    const stack = starts.map((s) => s.id);
    while (stack.length) {
      const id = stack.pop()!;
      if (seen.has(id)) continue;
      seen.add(id);
      for (const nx of adj.get(id) ?? []) stack.push(nx);
    }
    for (const n of nodes) {
      if (n.type !== "start" && !seen.has(n.id))
        issues.push({ severity: "warn", nodeId: n.id, message: `"${label(n)}" is unreachable from Start.` });
    }
  }

  // cycle detection (DFS with recursion stack)
  const WHITE = 0, GRAY = 1, BLACK = 2;
  const color = new Map<string, number>(nodes.map((n) => [n.id, WHITE]));
  let hasCycle = false;
  const visit = (id: string) => {
    color.set(id, GRAY);
    for (const nx of adj.get(id) ?? []) {
      const c = color.get(nx);
      if (c === GRAY) hasCycle = true;
      else if (c === WHITE) visit(nx);
    }
    color.set(id, BLACK);
  };
  for (const n of nodes) if (color.get(n.id) === WHITE) visit(n.id);
  if (hasCycle) issues.push({ severity: "error", message: "The graph contains a cycle." });

  // missing required params per node spec
  for (const n of nodes) {
    const spec = specByType.get(n.type);
    if (!spec) continue;
    for (const f of spec.fields) {
      if (f.required && isEmpty(n.data?.[f.name]))
        issues.push({ severity: "error", nodeId: n.id, message: `"${label(n)}" is missing required "${f.label}".` });
    }
  }

  return issues;
}

function label(n: CanvasNode): string {
  return String(n.data?.name ?? n.type);
}

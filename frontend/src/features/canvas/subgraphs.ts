// Reusable canvas blocks (F31): save a graph fragment as a named block and insert clones of it.
// Persisted to localStorage. cloneBlock is pure (id generator injectable) so it's unit-tested.

import type { CanvasEdge, CanvasNode } from "@/shared/api/client";

export interface SubgraphBlock {
  id: string;
  name: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
}

const KEY = "nexus_canvas_blocks";

export function loadBlocks(): SubgraphBlock[] {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) || "[]");
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

export function saveBlock(block: SubgraphBlock): SubgraphBlock[] {
  const next = [...loadBlocks().filter((b) => b.id !== block.id), block];
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    /* ignore */
  }
  return next;
}

export function removeBlock(id: string): SubgraphBlock[] {
  const next = loadBlocks().filter((b) => b.id !== id);
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    /* ignore */
  }
  return next;
}

let counter = 0;
const defaultGen = (type: string) => `${type}_${Date.now().toString(36)}${(counter++).toString(36)}`;

/** Clone a block's nodes+edges with fresh ids (edges remapped) and a position offset. Pure. */
export function cloneBlock(
  block: SubgraphBlock,
  offset = 40,
  genId: (type: string) => string = defaultGen,
): { nodes: CanvasNode[]; edges: CanvasEdge[] } {
  const idMap = new Map<string, string>();
  const nodes = block.nodes.map((n) => {
    const nid = genId(n.type);
    idMap.set(n.id, nid);
    return { ...n, id: nid, position: { x: n.position.x + offset, y: n.position.y + offset }, data: { ...n.data } };
  });
  const edges = block.edges.map((e) => ({
    source: idMap.get(e.source) ?? e.source,
    target: idMap.get(e.target) ?? e.target,
    sourceHandle: e.sourceHandle,
    targetHandle: e.targetHandle,
  }));
  return { nodes, edges };
}

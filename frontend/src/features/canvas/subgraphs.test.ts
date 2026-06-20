import { describe, expect, it } from "vitest";
import type { CanvasEdge, CanvasNode } from "@/shared/api/client";
import { cloneBlock, type SubgraphBlock } from "./subgraphs";

const node = (id: string, type: string): CanvasNode => ({ id, type, position: { x: 10, y: 20 }, data: { name: id } });
const edge = (source: string, target: string): CanvasEdge => ({ source, target, sourceHandle: "output" });

const block: SubgraphBlock = {
  id: "b1",
  name: "Block",
  nodes: [node("a", "start"), node("b", "automation_task")],
  edges: [edge("a", "b")],
};

describe("cloneBlock", () => {
  it("assigns fresh ids, remaps edges, and offsets positions", () => {
    let n = 0;
    const cloned = cloneBlock(block, 50, (t) => `${t}_${n++}`);
    expect(cloned.nodes.map((x) => x.id)).toEqual(["start_0", "automation_task_1"]);
    expect(cloned.nodes[0].position).toEqual({ x: 60, y: 70 });
    // the edge is remapped to the new ids
    expect(cloned.edges[0]).toMatchObject({ source: "start_0", target: "automation_task_1", sourceHandle: "output" });
  });

  it("preserves node count and data", () => {
    const cloned = cloneBlock(block, 0, (t) => `${t}_x`);
    expect(cloned.nodes).toHaveLength(2);
    expect(cloned.nodes[0].data.name).toBe("a");
  });
});

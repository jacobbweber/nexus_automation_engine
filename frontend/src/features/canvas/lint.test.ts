import { describe, expect, it } from "vitest";
import type { CanvasEdge, CanvasNode, NodeTypeSpec } from "@/shared/api/client";
import { lintGraph } from "./lint";

const specs: NodeTypeSpec[] = [
  { type: "start", label: "Start", category: "Flow", description: "", fields: [], outputs: ["output"] },
  { type: "end", label: "End", category: "Flow", description: "", fields: [], outputs: [] },
  {
    type: "automation_task", label: "Task", category: "Backend", description: "",
    fields: [{ name: "connector", type: "select", label: "Connector", required: true, default: null, choices: null, help: "", source: "execution_connectors", placeholder: "" }],
    outputs: ["output"],
  },
];

const node = (id: string, type: string, data: Record<string, unknown> = {}): CanvasNode => ({ id, type, position: { x: 0, y: 0 }, data });
const edge = (source: string, target: string): CanvasEdge => ({ source, target });

describe("lintGraph", () => {
  it("passes a valid start→task→end graph", () => {
    const nodes = [node("s", "start"), node("t", "automation_task", { connector: "ansible" }), node("e", "end")];
    const edges = [edge("s", "t"), edge("t", "e")];
    const issues = lintGraph(nodes, edges, specs);
    expect(issues).toEqual([]);
  });

  it("flags a missing required parameter", () => {
    const nodes = [node("s", "start"), node("t", "automation_task", {}), node("e", "end")];
    const edges = [edge("s", "t"), edge("t", "e")];
    const issues = lintGraph(nodes, edges, specs);
    expect(issues.some((i) => i.message.includes("Connector") && i.nodeId === "t")).toBe(true);
  });

  it("flags unreachable nodes and missing start", () => {
    const nodes = [node("a", "automation_task", { connector: "x" }), node("b", "automation_task", { connector: "y" })];
    const issues = lintGraph(nodes, [], specs);
    expect(issues.some((i) => i.message.includes("No Start"))).toBe(true);
  });

  it("detects a cycle", () => {
    const nodes = [node("s", "start"), node("a", "automation_task", { connector: "x" }), node("b", "automation_task", { connector: "y" })];
    const edges = [edge("s", "a"), edge("a", "b"), edge("b", "a")];
    const issues = lintGraph(nodes, edges, specs);
    expect(issues.some((i) => i.message.includes("cycle"))).toBe(true);
  });

  it("flags dangling edges", () => {
    const nodes = [node("s", "start"), node("e", "end")];
    const edges = [edge("s", "ghost")];
    const issues = lintGraph(nodes, edges, specs);
    expect(issues.some((i) => i.message.includes("missing node"))).toBe(true);
  });
});

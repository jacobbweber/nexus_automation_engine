import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Canvas, Connectors, openSocket, type Capabilities, type CanvasEdge, type CanvasNode, type NodeTypeSpec, type Workflow } from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Button } from "@/shared/ui/primitives";
import { ACCENT_BY_TYPE, NODE_CATEGORIES, defaultData } from "./nodeTypes";
import { SchemaProperties } from "./SchemaForm";
import { lintGraph } from "./lint";

// Builds a node's initial data from its schema defaults so new nodes start fully populated.
function defaultFromSpec(spec: NodeTypeSpec | undefined, type: string): Record<string, unknown> {
  if (!spec) return defaultData(type);
  const data: Record<string, unknown> = { name: spec.label };
  for (const f of spec.fields) {
    if (f.default !== null && f.default !== undefined) data[f.name] = f.default;
    else if (f.type === "keyvalue") data[f.name] = {};
    else if (["assignments", "cases", "inputs", "multiselect"].includes(f.type)) data[f.name] = [];
  }
  return data;
}

const NODE_W = 172;
const NODE_H = 62;

type StepStatus = "running" | "completed" | "failed" | "skipped";

export function CanvasPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [currentId, setCurrentId] = useState<string | undefined>();
  const [name, setName] = useState("Untitled workflow");
  const [team, setTeam] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [owner, setOwner] = useState("");
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [edges, setEdges] = useState<CanvasEdge[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<{ nodeId: string; handle: string } | null>(null);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [zoom, setZoom] = useState(1);
  const [nodeStates, setNodeStates] = useState<Record<string, StepStatus>>({});
  const [approval, setApproval] = useState<{ run_id: string; node_id: string; message: string } | null>(null);
  const [runForm, setRunForm] = useState<Record<string, unknown> | null>(null);
  const [caps, setCaps] = useState<Capabilities[]>([]);
  const [specs, setSpecs] = useState<NodeTypeSpec[]>([]);
  const [running, setRunning] = useState(false);

  const dragRef = useRef<{ id: string; ox: number; oy: number } | null>(null);
  const panRef = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    Canvas.list().then(setWorkflows).catch(() => undefined);
    Connectors.list().then(setCaps).catch(() => undefined);
    Canvas.nodeTypes().then(setSpecs).catch(() => undefined);
  }, []);

  const specFor = (type: string) => specs.find((s) => s.type === type);

  const onMouseMove = useCallback((e: MouseEvent) => {
    if (dragRef.current) {
      const { id, ox, oy } = dragRef.current;
      setNodes((ns) =>
        ns.map((n) =>
          n.id === id ? { ...n, position: { x: e.clientX / zoom - ox, y: e.clientY / zoom - oy } } : n,
        ),
      );
    } else if (panRef.current) {
      setPan({ x: e.clientX - panRef.current.x, y: e.clientY - panRef.current.y });
    }
  }, [zoom]);

  const onMouseUp = useCallback(() => {
    dragRef.current = null;
    panRef.current = null;
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [onMouseMove, onMouseUp]);

  function addNode(type: string) {
    const id = `${type}_${Math.random().toString(36).slice(2, 7)}`;
    const x = (200 - pan.x) / zoom + Math.random() * 60;
    const y = (160 - pan.y) / zoom + Math.random() * 60;
    setNodes((ns) => [...ns, { id, type, position: { x, y }, data: defaultFromSpec(specFor(type), type) }]);
  }

  function startConnect(nodeId: string, handle: string, e: React.MouseEvent) {
    e.stopPropagation();
    setConnecting({ nodeId, handle });
  }

  function finishConnect(targetId: string) {
    if (connecting && connecting.nodeId !== targetId) {
      setEdges((es) => [
        ...es.filter((x) => !(x.target === targetId && x.source === connecting.nodeId)),
        { source: connecting.nodeId, target: targetId, sourceHandle: connecting.handle },
      ]);
    }
    setConnecting(null);
  }

  async function save() {
    const wf = await Canvas.save({
      id: currentId,
      name,
      graph: { nodes, edges, viewport: { x: pan.x, y: pan.y, zoom } },
      owner: owner || user?.username,
      team,
      tags,
    });
    setCurrentId(wf.id);
    setOwner(wf.owner);
    Canvas.list().then(setWorkflows);
  }

  const load = useCallback(async (id: string) => {
    const wf = await Canvas.get(id);
    setCurrentId(wf.id);
    setName(wf.name);
    setTeam(wf.team);
    setTags(wf.tags);
    setOwner(wf.owner);
    setNodes(wf.graph.nodes);
    setEdges(wf.graph.edges);
    setNodeStates({});
  }, []);

  // Deep-link from the Workflow Library: /canvas?id=<wf> auto-loads that workflow.
  useEffect(() => {
    const id = params.get("id");
    if (id && id !== currentId) load(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, load]);

  function newWorkflow() {
    setCurrentId(undefined);
    setName("Untitled workflow");
    setTeam("");
    setTags([]);
    setOwner("");
    setNodes([]);
    setEdges([]);
    setNodeStates({});
    if (params.get("id")) setParams({}, { replace: true });
  }

  async function submitForReview() {
    let id = currentId;
    if (!id) id = (await Canvas.save({ name, graph: { nodes, edges, viewport: {} } })).id;
    await Canvas.submitForReview(id);
    setCurrentId(id);
    Canvas.list().then(setWorkflows);
  }

  // The Start node's declared inputs (ad-hoc run parameters the operator supplies at launch).
  function startInputs(): { name: string; type: string; default: unknown }[] {
    const start = nodes.find((n) => n.type === "start");
    const raw = (start?.data.inputs as { name: string; type: string; default: unknown }[]) ?? [];
    return raw.filter((i) => i && i.name);
  }

  function runClicked() {
    const inputs = startInputs();
    if (inputs.length > 0) {
      const seed: Record<string, unknown> = {};
      for (const i of inputs) seed[i.name] = i.default ?? "";
      setRunForm(seed);
    } else {
      void doRun({});
    }
  }

  async function doRun(inputs: Record<string, unknown>) {
    setRunForm(null);
    if (!currentId) await save();
    const id = currentId ?? (await Canvas.save({ name, graph: { nodes, edges, viewport: {} } })).id;
    setNodeStates({});
    setRunning(true);
    const { run_id } = await Canvas.run(id, inputs);
    const ws = openSocket(`/canvas/runs/${run_id}/stream`);
    ws.onmessage = (ev) => {
      const d = JSON.parse(ev.data);
      if (d.type === "step" && d.node_id) {
        setNodeStates((s) => ({ ...s, [d.node_id]: d.status }));
      } else if (d.type === "approval_required") {
        setApproval({ run_id, node_id: d.node_id, message: d.message });
      } else if (d.type === "run_completed" || d.type === "run_failed") {
        setRunning(false);
        ws.close();
      }
    };
    ws.onclose = () => setRunning(false);
  }

  async function resolveApproval(approved: boolean) {
    if (!approval) return;
    await Canvas.resolveApproval(approval.run_id, approval.node_id, approved);
    setApproval(null);
  }

  const selected = nodes.find((n) => n.id === selectedId) ?? null;
  const lint = useMemo(() => lintGraph(nodes, edges, specs), [nodes, edges, specs]);
  const lintErrors = lint.filter((i) => i.severity === "error").length;

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <Palette onAdd={addNode} />
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Toolbar
          name={name}
          setName={setName}
          team={team}
          setTeam={setTeam}
          tags={tags}
          setTags={setTags}
          owner={owner}
          workflows={workflows}
          currentId={currentId}
          onLoad={load}
          onNew={newWorkflow}
          onSave={save}
          onRun={runClicked}
          onSubmit={submitForReview}
          running={running}
        />
        {lint.length > 0 && (
          <div style={{ display: "flex", gap: 12, alignItems: "center", padding: "6px 14px", borderBottom: "1px solid var(--border)", background: lintErrors ? "var(--danger-soft)" : "var(--warn-soft)", fontSize: "0.78rem", flexWrap: "wrap" }}>
            <span style={{ fontWeight: 600 }}>
              {lintErrors > 0 ? `${lintErrors} error${lintErrors > 1 ? "s" : ""}` : `${lint.length} warning${lint.length > 1 ? "s" : ""}`}
            </span>
            {lint.slice(0, 4).map((iss, i) => (
              <button
                key={i}
                onClick={() => iss.nodeId && setSelectedId(iss.nodeId)}
                style={{ background: "none", border: "none", color: iss.severity === "error" ? "var(--danger)" : "var(--warn)", cursor: iss.nodeId ? "pointer" : "default", fontSize: "0.76rem", padding: 0 }}
              >
                • {iss.message}
              </button>
            ))}
            {lint.length > 4 && <span style={{ color: "var(--text-muted)" }}>+{lint.length - 4} more</span>}
          </div>
        )}
        <div
          onWheel={(e) => setZoom((z) => Math.min(2.2, Math.max(0.4, z - e.deltaY * 0.001)))}
          onMouseDown={(e) => {
            panRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
            setSelectedId(null);
          }}
          style={{ position: "relative", flex: 1, overflow: "hidden", background: "var(--bg)", cursor: panRef.current ? "grabbing" : "default" }}
        >
          <div style={{ position: "absolute", transformOrigin: "0 0", transform: `translate(${pan.x}px,${pan.y}px) scale(${zoom})` }}>
            <Edges nodes={nodes} edges={edges} />
            {nodes.map((n) => (
              <NodeBox
                key={n.id}
                node={n}
                accent={ACCENT_BY_TYPE[n.type] ?? "var(--text-muted)"}
                outputs={specFor(n.type)?.outputs ?? ["output"]}
                state={nodeStates[n.id]}
                selected={selectedId === n.id}
                connecting={!!connecting}
                onSelect={() => setSelectedId(n.id)}
                onDragStart={(e) => {
                  dragRef.current = { id: n.id, ox: e.clientX / zoom - n.position.x, oy: e.clientY / zoom - n.position.y };
                }}
                onStartConnect={(handle, e) => startConnect(n.id, handle, e)}
                onFinishConnect={() => finishConnect(n.id)}
              />
            ))}
          </div>
          <div style={{ position: "absolute", bottom: 10, left: 12, fontSize: "0.72rem", color: "var(--text-muted)" }}>
            {Math.round(zoom * 100)}% · {nodes.length} nodes · {edges.length} edges
            {connecting && " · click a target node to connect"}
          </div>
        </div>
      </div>
      <div style={{ width: 300, borderLeft: "1px solid var(--border)", background: "var(--surface)", padding: 16, overflow: "auto" }}>
        {selected ? (
          <>
            <div style={{ fontSize: "0.66rem", textTransform: "uppercase", color: ACCENT_BY_TYPE[selected.type] ?? "var(--text-muted)", fontWeight: 700 }}>
              {specFor(selected.type)?.label ?? selected.type}
            </div>
            <SchemaProperties
              node={selected}
              spec={specFor(selected.type)}
              caps={caps}
              workflows={workflows}
              onChange={(data) => setNodes((ns) => ns.map((n) => (n.id === selectedId ? { ...n, data } : n)))}
              onDelete={() => { setNodes((ns) => ns.filter((n) => n.id !== selectedId)); setEdges((es) => es.filter((e) => e.source !== selectedId && e.target !== selectedId)); setSelectedId(null); }}
            />
          </>
        ) : (
          <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Select a node to edit its properties.</div>
        )}
      </div>
      {approval && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "grid", placeItems: "center" }}>
          <div style={{ width: 380, padding: 24, borderRadius: 12, background: "var(--surface)", border: "1px solid var(--border)" }}>
            <h3 style={{ marginTop: 0 }}>Approval required</h3>
            <p style={{ color: "var(--text-muted)" }}>{approval.message}</p>
            <div style={{ display: "flex", gap: 10 }}>
              <Button onClick={() => resolveApproval(true)}>Approve</Button>
              <Button variant="ghost" onClick={() => resolveApproval(false)}>Reject</Button>
            </div>
          </div>
        </div>
      )}
      {runForm && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "grid", placeItems: "center" }}>
          <div style={{ width: 400, padding: 24, borderRadius: 12, background: "var(--surface)", border: "1px solid var(--border)" }}>
            <h3 style={{ marginTop: 0 }}>Run inputs</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.82rem", marginTop: 0 }}>
              Supply the workflow's declared inputs for this run.
            </p>
            {startInputs().map((i) => (
              <label key={i.name} style={{ display: "block", margin: "10px 0" }}>
                <span style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>{i.name} <em style={{ opacity: 0.7 }}>({i.type})</em></span>
                <input
                  type={i.type === "number" ? "number" : "text"}
                  value={String(runForm[i.name] ?? "")}
                  onChange={(e) => setRunForm({ ...runForm, [i.name]: i.type === "number" ? Number(e.target.value) : e.target.value })}
                  style={{ width: "100%", marginTop: 4, padding: "7px 9px", borderRadius: 7, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                />
              </label>
            ))}
            <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
              <Button onClick={() => doRun(runForm)}>▶ Run</Button>
              <Button variant="ghost" onClick={() => setRunForm(null)}>Cancel</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Palette({ onAdd }: { onAdd: (t: string) => void }) {
  return (
    <div style={{ width: 200, borderRight: "1px solid var(--border)", background: "var(--surface)", padding: 12, overflow: "auto" }}>
      {NODE_CATEGORIES.map((cat) => (
        <div key={cat.name} style={{ marginBottom: 14 }}>
          <div style={{ fontSize: "0.68rem", textTransform: "uppercase", color: cat.color, marginBottom: 6 }}>{cat.name}</div>
          {cat.types.map((t) => (
            <button
              key={t.type}
              title={t.desc}
              onClick={() => onAdd(t.type)}
              style={{ display: "block", width: "100%", textAlign: "left", padding: "7px 9px", marginBottom: 4, borderRadius: 7, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", cursor: "pointer", fontSize: "0.8rem" }}
            >
              {t.label}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

function Toolbar(props: {
  name: string;
  setName: (v: string) => void;
  team: string;
  setTeam: (v: string) => void;
  tags: string[];
  setTags: (v: string[]) => void;
  owner: string;
  workflows: Workflow[];
  currentId?: string;
  onLoad: (id: string) => void;
  onNew: () => void;
  onSave: () => void;
  onRun: () => void;
  onSubmit: () => void;
  running: boolean;
}) {
  const tb: React.CSSProperties = { padding: "7px 10px", borderRadius: 7, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" };
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", padding: "10px 14px", borderBottom: "1px solid var(--border)", background: "var(--surface)", flexWrap: "wrap" }}>
      <input value={props.name} onChange={(e) => props.setName(e.target.value)} placeholder="Workflow name" style={{ ...tb, width: 180 }} />
      <input value={props.team} onChange={(e) => props.setTeam(e.target.value)} placeholder="Team" style={{ ...tb, width: 110 }} />
      <input value={props.tags.join(", ")} onChange={(e) => props.setTags(e.target.value.split(",").map((t) => t.trim()).filter(Boolean))} placeholder="tags, comma-sep" style={{ ...tb, width: 150 }} />
      {props.owner && <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>owner: {props.owner}</span>}
      <select value={props.currentId ?? ""} onChange={(e) => e.target.value && props.onLoad(e.target.value)} style={tb}>
        <option value="">— open —</option>
        {props.workflows.map((w) => (
          <option key={w.id} value={w.id}>{w.name}</option>
        ))}
      </select>
      <Button variant="ghost" onClick={props.onNew}>New</Button>
      <Button variant="ghost" onClick={props.onSave}>Save</Button>
      <Button variant="ghost" onClick={props.onSubmit}>Submit for review</Button>
      <div style={{ marginLeft: "auto" }}>
        <Button onClick={props.onRun} disabled={props.running}>{props.running ? "Running…" : "▶ Run"}</Button>
      </div>
    </div>
  );
}

const STATE_COLOR: Record<StepStatus, string> = {
  running: "var(--color-accent)",
  completed: "var(--color-ok)",
  failed: "var(--color-danger)",
  skipped: "var(--text-muted)",
};

function handleColor(handle: string, accent: string): string {
  if (handle === "true") return "var(--color-ok)";
  if (handle === "false" || handle === "error") return "var(--color-danger)";
  return accent;
}

function handleLabel(handle: string): string {
  if (handle === "output") return "";
  if (handle === "true") return "T";
  if (handle === "false") return "F";
  if (handle.startsWith("case_")) return handle.replace("case_", "");
  return handle.slice(0, 3);
}

function NodeBox(props: {
  node: CanvasNode;
  accent: string;
  outputs: string[];
  state?: StepStatus;
  selected: boolean;
  connecting: boolean;
  onSelect: () => void;
  onDragStart: (e: React.MouseEvent) => void;
  onStartConnect: (handle: string, e: React.MouseEvent) => void;
  onFinishConnect: () => void;
}) {
  const { node, accent, state, outputs } = props;
  const border = state ? STATE_COLOR[state] : props.selected ? "var(--color-accent)" : "var(--border)";
  // Stack output handles down the right edge; "error" is always offered for retry/recovery edges.
  const handles = outputs.includes("error") ? outputs : [...outputs, "error"];
  const height = Math.max(NODE_H, handles.length * 20 + 24);
  return (
    <div
      onMouseDown={(e) => { e.stopPropagation(); props.onDragStart(e); }}
      onClick={(e) => {
        e.stopPropagation();
        if (props.connecting) props.onFinishConnect();
        else props.onSelect();
      }}
      style={{ position: "absolute", left: node.position.x, top: node.position.y, width: NODE_W, minHeight: height, padding: "8px 10px", borderRadius: 9, border: `2px solid ${border}`, background: "var(--surface)", boxShadow: "0 1px 4px rgba(0,0,0,0.25)", cursor: "grab", userSelect: "none" }}
    >
      <div style={{ fontSize: "0.62rem", textTransform: "uppercase", color: accent, fontWeight: 700 }}>{node.type}</div>
      <div style={{ fontSize: "0.84rem" }}>{String(node.data.name ?? node.id)}</div>
      {/* input handle */}
      <span style={{ position: "absolute", left: -7, top: height / 2 - 6, width: 12, height: 12, borderRadius: "50%", background: "var(--border)" }} />
      {/* output handle(s) — one per declared branch + error */}
      {handles.map((h, i) => (
        <Handle
          key={h}
          label={handleLabel(h)}
          title={h}
          color={handleColor(h, accent)}
          top={handles.length === 1 ? height / 2 - 7 : 16 + i * 20}
          onClick={(e) => props.onStartConnect(h, e)}
        />
      ))}
    </div>
  );
}

function Handle({ label, title, color, top, onClick }: { label: string; title: string; color: string; top: number; onClick: (e: React.MouseEvent) => void }) {
  return (
    <span
      onClick={onClick}
      title={`${title} — click to start a connection`}
      style={{ position: "absolute", right: -8, top, width: 14, height: 14, borderRadius: "50%", background: color, cursor: "crosshair", fontSize: 8, color: "#000", display: "grid", placeItems: "center", fontWeight: 700 }}
    >
      {label}
    </span>
  );
}

function Edges({ nodes, edges }: { nodes: CanvasNode[]; edges: CanvasEdge[] }) {
  const pos = (id: string) => nodes.find((n) => n.id === id)?.position;
  return (
    <svg style={{ position: "absolute", width: 4000, height: 3000, pointerEvents: "none", overflow: "visible" }}>
      {edges.map((e, i) => {
        const s = pos(e.source);
        const t = pos(e.target);
        if (!s || !t) return null;
        const x1 = s.x + NODE_W;
        const y1 = s.y + NODE_H / 2;
        const x2 = t.x;
        const y2 = t.y + NODE_H / 2;
        const color = e.sourceHandle === "true" ? "rgba(95,169,127,0.7)" : e.sourceHandle === "false" || e.sourceHandle === "error" ? "rgba(208,107,92,0.7)" : "rgba(120,140,160,0.6)";
        const mid = (x1 + x2) / 2;
        return (
          <path key={i} d={`M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`} stroke={color} strokeWidth={2} fill="none" />
        );
      })}
    </svg>
  );
}


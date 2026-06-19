import { useCallback, useEffect, useRef, useState } from "react";
import { Canvas, Connectors, openSocket, type Capabilities, type CanvasEdge, type CanvasNode, type Workflow } from "@/shared/api/client";
import { Button } from "@/shared/ui/primitives";
import { ACCENT_BY_TYPE, NODE_CATEGORIES, defaultData } from "./nodeTypes";

const NODE_W = 172;
const NODE_H = 62;

type StepStatus = "running" | "completed" | "failed" | "skipped";

export function CanvasPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [currentId, setCurrentId] = useState<string | undefined>();
  const [name, setName] = useState("Untitled workflow");
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [edges, setEdges] = useState<CanvasEdge[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<{ nodeId: string; handle: string } | null>(null);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [zoom, setZoom] = useState(1);
  const [nodeStates, setNodeStates] = useState<Record<string, StepStatus>>({});
  const [approval, setApproval] = useState<{ run_id: string; node_id: string; message: string } | null>(null);
  const [caps, setCaps] = useState<Capabilities[]>([]);
  const [running, setRunning] = useState(false);

  const dragRef = useRef<{ id: string; ox: number; oy: number } | null>(null);
  const panRef = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    Canvas.list().then(setWorkflows).catch(() => undefined);
    Connectors.list().then(setCaps).catch(() => undefined);
  }, []);

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
    setNodes((ns) => [...ns, { id, type, position: { x, y }, data: defaultData(type) }]);
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
    });
    setCurrentId(wf.id);
    Canvas.list().then(setWorkflows);
  }

  async function load(id: string) {
    const wf = await Canvas.get(id);
    setCurrentId(wf.id);
    setName(wf.name);
    setNodes(wf.graph.nodes);
    setEdges(wf.graph.edges);
    setNodeStates({});
  }

  function newWorkflow() {
    setCurrentId(undefined);
    setName("Untitled workflow");
    setNodes([]);
    setEdges([]);
    setNodeStates({});
  }

  async function run() {
    if (!currentId) await save();
    const id = currentId ?? (await Canvas.save({ name, graph: { nodes, edges, viewport: {} } })).id;
    setNodeStates({});
    setRunning(true);
    const { run_id } = await Canvas.run(id, {});
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

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <Palette onAdd={addNode} />
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Toolbar
          name={name}
          setName={setName}
          workflows={workflows}
          currentId={currentId}
          onLoad={load}
          onNew={newWorkflow}
          onSave={save}
          onRun={run}
          running={running}
        />
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
      <Properties node={selected} caps={caps} onChange={(data) => setNodes((ns) => ns.map((n) => (n.id === selectedId ? { ...n, data } : n)))} onDelete={() => { setNodes((ns) => ns.filter((n) => n.id !== selectedId)); setEdges((es) => es.filter((e) => e.source !== selectedId && e.target !== selectedId)); setSelectedId(null); }} />
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
  workflows: Workflow[];
  currentId?: string;
  onLoad: (id: string) => void;
  onNew: () => void;
  onSave: () => void;
  onRun: () => void;
  running: boolean;
}) {
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "center", padding: "10px 14px", borderBottom: "1px solid var(--border)", background: "var(--surface)" }}>
      <input value={props.name} onChange={(e) => props.setName(e.target.value)} style={{ padding: "7px 10px", borderRadius: 7, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }} />
      <select value={props.currentId ?? ""} onChange={(e) => e.target.value && props.onLoad(e.target.value)} style={{ padding: "7px", borderRadius: 7, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}>
        <option value="">— open —</option>
        {props.workflows.map((w) => (
          <option key={w.id} value={w.id}>{w.name}</option>
        ))}
      </select>
      <Button variant="ghost" onClick={props.onNew}>New</Button>
      <Button variant="ghost" onClick={props.onSave}>Save</Button>
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

function NodeBox(props: {
  node: CanvasNode;
  accent: string;
  state?: StepStatus;
  selected: boolean;
  connecting: boolean;
  onSelect: () => void;
  onDragStart: (e: React.MouseEvent) => void;
  onStartConnect: (handle: string, e: React.MouseEvent) => void;
  onFinishConnect: () => void;
}) {
  const { node, accent, state } = props;
  const border = state ? STATE_COLOR[state] : props.selected ? "var(--color-accent)" : "var(--border)";
  const isCondition = node.type === "condition";
  return (
    <div
      onMouseDown={(e) => { e.stopPropagation(); props.onDragStart(e); }}
      onClick={(e) => {
        e.stopPropagation();
        if (props.connecting) props.onFinishConnect();
        else props.onSelect();
      }}
      style={{ position: "absolute", left: node.position.x, top: node.position.y, width: NODE_W, minHeight: NODE_H, padding: "8px 10px", borderRadius: 9, border: `2px solid ${border}`, background: "var(--surface)", boxShadow: "0 1px 4px rgba(0,0,0,0.25)", cursor: "grab", userSelect: "none" }}
    >
      <div style={{ fontSize: "0.62rem", textTransform: "uppercase", color: accent, fontWeight: 700 }}>{node.type}</div>
      <div style={{ fontSize: "0.84rem" }}>{String(node.data.name ?? node.id)}</div>
      {/* input handle */}
      <span style={{ position: "absolute", left: -7, top: NODE_H / 2 - 6, width: 12, height: 12, borderRadius: "50%", background: "var(--border)" }} />
      {/* output handle(s) */}
      {isCondition ? (
        <>
          <Handle label="T" color="var(--color-ok)" top={6} onClick={(e) => props.onStartConnect("true", e)} />
          <Handle label="F" color="var(--color-danger)" top={NODE_H - 4} onClick={(e) => props.onStartConnect("false", e)} />
        </>
      ) : (
        <Handle label="" color={accent} top={NODE_H / 2 - 6} onClick={(e) => props.onStartConnect("output", e)} />
      )}
    </div>
  );
}

function Handle({ label, color, top, onClick }: { label: string; color: string; top: number; onClick: (e: React.MouseEvent) => void }) {
  return (
    <span
      onClick={onClick}
      title="Click to start a connection"
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

function Properties({ node, caps, onChange, onDelete }: {
  node: CanvasNode | null;
  caps: Capabilities[];
  onChange: (data: Record<string, unknown>) => void;
  onDelete: () => void;
}) {
  if (!node) {
    return (
      <div style={{ width: 280, borderLeft: "1px solid var(--border)", background: "var(--surface)", padding: 16, color: "var(--text-muted)", fontSize: "0.85rem" }}>
        Select a node to edit its properties.
      </div>
    );
  }
  const data = node.data;
  const set = (k: string, v: unknown) => onChange({ ...data, [k]: v });
  const execCaps = caps.filter((c) => c.category === "execution");
  const activeConn = execCaps.find((c) => c.kind === data.connector);

  return (
    <div style={{ width: 280, borderLeft: "1px solid var(--border)", background: "var(--surface)", padding: 16, overflow: "auto" }}>
      <div style={{ fontSize: "0.66rem", textTransform: "uppercase", color: "var(--text-muted)" }}>{node.type}</div>
      <Input label="Name" value={String(data.name ?? "")} onChange={(v) => set("name", v)} />

      {node.type === "automation_task" && (
        <>
          <Select label="Connector" value={String(data.connector ?? "")} options={execCaps.map((c) => c.kind)} onChange={(v) => set("connector", v)} />
          <Select label="Action" value={String(data.action ?? "")} options={(activeConn?.actions ?? []).map((a) => a.name)} onChange={(v) => set("action", v)} />
          <JsonArea label="Params (JSON)" value={data.params ?? {}} onChange={(v) => set("params", v)} />
          <Check label="Check mode" value={!!data.check_mode} onChange={(v) => set("check_mode", v)} />
        </>
      )}
      {node.type === "condition" && (
        <>
          <Input label="Variable" value={String(data.variable ?? "")} onChange={(v) => set("variable", v)} />
          <Select label="Operator" value={String(data.operator ?? "==")} options={["==", "!=", ">", "<", "contains", "is_empty"]} onChange={(v) => set("operator", v)} />
          <Input label="Value" value={String(data.value ?? "")} onChange={(v) => set("value", v)} />
        </>
      )}
      {!["automation_task", "condition", "start"].includes(node.type) && (
        <JsonArea label="Data (JSON)" value={data} onChange={onChange} />
      )}

      <div style={{ marginTop: 14 }}>
        <Button variant="ghost" onClick={onDelete}>Delete node</Button>
      </div>
    </div>
  );
}

function Input({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label style={{ display: "block", margin: "10px 0" }}>
      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} style={ctl} />
    </label>
  );
}
function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <label style={{ display: "block", margin: "10px 0" }}>
      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} style={ctl}>
        <option value="">—</option>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}
function Check({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label style={{ display: "flex", gap: 8, alignItems: "center", margin: "10px 0", fontSize: "0.82rem" }}>
      <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} /> {label}
    </label>
  );
}
function JsonArea({ label, value, onChange }: { label: string; value: unknown; onChange: (v: Record<string, unknown>) => void }) {
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
        rows={6}
        style={{ ...ctl, fontFamily: "ui-monospace, monospace", fontSize: "0.75rem", borderColor: err ? "var(--color-danger)" : "var(--border)" }}
      />
    </label>
  );
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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Canvas, Catalog, Connectors, openSocket, type Capabilities, type CanvasEdge, type CanvasNode, type NodeTypeSpec, type Template, type Workflow } from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Button } from "@/shared/ui/primitives";
import { ACCENT_BY_TYPE, NODE_CATEGORIES, defaultData } from "./nodeTypes";
import { SchemaProperties } from "./SchemaForm";
import { lintGraph } from "./lint";
import { cloneBlock, loadBlocks, removeBlock, saveBlock, type SubgraphBlock } from "./subgraphs";

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
  const [replayRunId, setReplayRunId] = useState<string | null>(null);
  const [blocks, setBlocks] = useState<SubgraphBlock[]>(() => loadBlocks());
  const [caps, setCaps] = useState<Capabilities[]>([]);
  const [specs, setSpecs] = useState<NodeTypeSpec[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  const dragRef = useRef<{ id: string; ox: number; oy: number } | null>(null);
  const panRef = useRef<{ x: number; y: number } | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const [nodeSearch, setNodeSearch] = useState("");

  useEffect(() => {
    Canvas.list().then(setWorkflows).catch(() => undefined);
    Connectors.list().then(setCaps).catch(() => undefined);
    Canvas.nodeTypes().then(setSpecs).catch(() => undefined);
    Catalog.list().then(setTemplates).catch(() => undefined);
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

  function saveAsBlock() {
    if (nodes.length === 0) return;
    const blockName = window.prompt("Name this reusable block:", "Block");
    if (!blockName) return;
    setBlocks(saveBlock({ id: `blk_${Date.now().toString(36)}`, name: blockName, nodes, edges }));
  }

  function insertBlock(block: SubgraphBlock) {
    const cloned = cloneBlock(block, 60);
    setNodes((ns) => [...ns, ...cloned.nodes]);
    setEdges((es) => [...es, ...cloned.edges]);
  }

  function deleteBlock(id: string) {
    setBlocks(removeBlock(id));
  }

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

  // Deep-link from the Workflow Library: /canvas?id=<wf> auto-loads that workflow; ?replay=<run>
  // plays that run's recorded step trace back onto the graph.
  useEffect(() => {
    const id = params.get("id");
    const replay = params.get("replay");
    if (id && id !== currentId) {
      load(id).then(() => {
        if (replay) void playReplay(replay);
      });
    } else if (replay && replay !== replayRunId) {
      void playReplay(replay);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, load]);

  async function playReplay(runId: string) {
    setReplayRunId(runId);
    setNodeStates({});
    const run = await Canvas.getRun(runId).catch(() => null);
    if (!run?.steps) {
      setReplayRunId(null);
      return;
    }
    const reduce = matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const steps = [...run.steps].sort((a, b) => (a.started_at ?? "").localeCompare(b.started_at ?? ""));
    for (const st of steps) {
      setNodeStates((s) => ({ ...s, [st.node_id]: st.status as StepStatus }));
      if (!reduce) await new Promise((r) => setTimeout(r, 500));
    }
  }

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

  function runClicked(plan = false) {
    const inputs = startInputs();
    if (inputs.length > 0) {
      const seed: Record<string, unknown> = {};
      for (const i of inputs) seed[i.name] = i.default ?? "";
      setRunForm({ __plan: plan, ...seed });
    } else {
      void doRun({}, plan);
    }
  }

  async function doRun(inputs: Record<string, unknown>, plan = false) {
    const { __plan, ...realInputs } = inputs as Record<string, unknown> & { __plan?: boolean };
    const isPlan = plan || __plan === true;
    setRunForm(null);
    if (!currentId) await save();
    const id = currentId ?? (await Canvas.save({ name, graph: { nodes, edges, viewport: {} } })).id;
    setNodeStates({});
    setRunError(null);
    setRunning(true);
    let run_id: string;
    try {
      ({ run_id } = await Canvas.run(id, realInputs, isPlan));
    } catch (e) {
      setRunning(false);
      setRunError(e instanceof Error ? e.message : "Run failed to dispatch.");
      return;
    }
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

  // --- comprehension aids (F26): fit-to-view, zoom controls, node search ---
  function fitView() {
    const box = canvasRef.current?.getBoundingClientRect();
    if (!box || nodes.length === 0) return;
    const xs = nodes.map((n) => n.position.x);
    const ys = nodes.map((n) => n.position.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs) + NODE_W;
    const minY = Math.min(...ys), maxY = Math.max(...ys) + NODE_H;
    const pad = 60;
    const z = Math.min(2.2, Math.max(0.4, Math.min((box.width - pad * 2) / (maxX - minX || 1), (box.height - pad * 2) / (maxY - minY || 1))));
    setZoom(z);
    setPan({ x: pad - minX * z, y: pad - minY * z });
  }

  function centerOn(node: CanvasNode) {
    const box = canvasRef.current?.getBoundingClientRect();
    if (!box) return;
    setPan({ x: box.width / 2 - (node.position.x + NODE_W / 2) * zoom, y: box.height / 2 - (node.position.y + NODE_H / 2) * zoom });
    setSelectedId(node.id);
  }

  const searchMatches = useMemo(() => {
    const q = nodeSearch.trim().toLowerCase();
    if (!q) return [];
    return nodes.filter((n) => String(n.data?.name ?? n.type).toLowerCase().includes(q)).slice(0, 6);
  }, [nodeSearch, nodes]);

  const selected = nodes.find((n) => n.id === selectedId) ?? null;
  const lint = useMemo(() => lintGraph(nodes, edges, specs), [nodes, edges, specs]);
  const lintErrors = lint.filter((i) => i.severity === "error").length;

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <Palette onAdd={addNode} blocks={blocks} onInsertBlock={insertBlock} onDeleteBlock={deleteBlock} onSaveBlock={saveAsBlock} />
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
          onRun={() => runClicked(false)}
          onDryRun={() => runClicked(true)}
          onSubmit={submitForReview}
          running={running}
        />
        {replayRunId && (
          <div style={{ display: "flex", gap: 10, alignItems: "center", padding: "6px 14px", borderBottom: "1px solid var(--border)", background: "var(--accent-soft)", fontSize: "0.78rem" }}>
            <span style={{ fontWeight: 600, color: "var(--accent)" }}>Replaying run {replayRunId.slice(0, 12)}…</span>
            <button onClick={() => playReplay(replayRunId)} style={{ background: "none", border: "none", color: "var(--accent)", cursor: "pointer", fontSize: "0.76rem" }}>↻ again</button>
            <button onClick={() => { setReplayRunId(null); setNodeStates({}); setParams({ ...(currentId ? { id: currentId } : {}) }, { replace: true }); }} style={{ marginLeft: "auto", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.76rem" }}>✕ exit replay</button>
          </div>
        )}
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
        {runError && (
          <div role="alert" style={{ display: "flex", gap: 12, alignItems: "center", padding: "6px 14px", borderBottom: "1px solid var(--border)", background: "var(--danger-soft)", fontSize: "0.78rem" }}>
            <span style={{ fontWeight: 600, color: "var(--danger)" }}>Run rejected</span>
            <span style={{ color: "var(--danger)" }}>{runError}</span>
            <button onClick={() => setRunError(null)} style={{ marginLeft: "auto", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.76rem" }}>✕ dismiss</button>
          </div>
        )}
        <div
          ref={canvasRef}
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

          {/* node search (top-right) */}
          <div onMouseDown={(e) => e.stopPropagation()} style={{ position: "absolute", top: 10, right: 12, width: 200 }}>
            <input
              value={nodeSearch}
              onChange={(e) => setNodeSearch(e.target.value)}
              placeholder="Find node…"
              aria-label="Find node"
              style={{ width: "100%", padding: "6px 9px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--surface)", color: "var(--text)", boxSizing: "border-box", fontSize: "0.78rem" }}
            />
            {searchMatches.length > 0 && (
              <div style={{ marginTop: 4, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-2)", overflow: "hidden" }}>
                {searchMatches.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => { centerOn(n); setNodeSearch(""); }}
                    style={{ display: "block", width: "100%", textAlign: "left", padding: "7px 10px", border: "none", background: "transparent", color: "var(--text)", cursor: "pointer", fontSize: "0.8rem" }}
                  >
                    {String(n.data?.name ?? n.type)}
                    <span style={{ color: "var(--text-muted)", fontSize: "0.68rem" }}> · {n.type}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* zoom / fit controls (bottom-right) */}
          <div onMouseDown={(e) => e.stopPropagation()} style={{ position: "absolute", bottom: 10, right: 12, display: "flex", gap: 4 }}>
            <CanvasCtl label="−" title="Zoom out" onClick={() => setZoom((z) => Math.max(0.4, z - 0.15))} />
            <CanvasCtl label="100%" title="Reset zoom" onClick={() => { setZoom(1); setPan({ x: 40, y: 40 }); }} />
            <CanvasCtl label="+" title="Zoom in" onClick={() => setZoom((z) => Math.min(2.2, z + 0.15))} />
            <CanvasCtl label="Fit" title="Fit to view" onClick={fitView} />
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
              templates={templates}
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

function CanvasCtl({ label, title, onClick }: { label: string; title: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      title={title}
      aria-label={title}
      style={{ minWidth: 30, height: 30, padding: "0 8px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--surface)", color: "var(--text)", cursor: "pointer", fontSize: "0.78rem", boxShadow: "var(--shadow-1)" }}
    >
      {label}
    </button>
  );
}

function Palette({ onAdd, blocks, onInsertBlock, onDeleteBlock, onSaveBlock }: {
  onAdd: (t: string) => void;
  blocks: SubgraphBlock[];
  onInsertBlock: (b: SubgraphBlock) => void;
  onDeleteBlock: (id: string) => void;
  onSaveBlock: () => void;
}) {
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

      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 6 }}>Blocks</div>
        {blocks.map((b) => (
          <div key={b.id} style={{ display: "flex", gap: 4, marginBottom: 4 }}>
            <button
              title={`Insert ${b.nodes.length} nodes`}
              onClick={() => onInsertBlock(b)}
              style={{ flex: 1, textAlign: "left", padding: "7px 9px", borderRadius: 7, border: "1px dashed var(--border)", background: "var(--bg)", color: "var(--text)", cursor: "pointer", fontSize: "0.8rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
            >
              {b.name} <span style={{ color: "var(--text-muted)", fontSize: "0.68rem" }}>·{b.nodes.length}</span>
            </button>
            <button onClick={() => onDeleteBlock(b.id)} aria-label={`Delete block ${b.name}`} title="Delete block" style={{ flex: "0 0 26px", borderRadius: 7, border: "1px solid var(--border)", background: "transparent", color: "var(--text-muted)", cursor: "pointer" }}>×</button>
          </div>
        ))}
        <button
          onClick={onSaveBlock}
          style={{ width: "100%", padding: "6px 8px", borderRadius: 7, border: "1px dashed var(--border)", background: "transparent", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.74rem" }}
        >
          + Save graph as block
        </button>
      </div>
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
  onDryRun: () => void;
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
      <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
        <Button variant="ghost" onClick={props.onDryRun} disabled={props.running} title="Run with all tasks in check mode — nothing mutates">Dry run</Button>
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


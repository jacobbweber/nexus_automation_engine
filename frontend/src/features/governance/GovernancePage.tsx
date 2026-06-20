import { useEffect, useState } from "react";
import {
  Canvas,
  ChangeApi,
  Schedules,
  Validation,
  type ChangeRecord,
  type ChangeTemplate,
  type ReviewStatus,
  type Schedule,
  type ValidationPolicy,
  type Workflow,
} from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Button, Card, Page, StatusBadge } from "@/shared/ui/primitives";
import { ChangeCalendar } from "./ChangeCalendar";
import { ValidationPolicyEditor } from "./ValidationPolicyEditor";

export function GovernancePage() {
  const { user } = useAuth();
  const canReview = user?.global_role === "engineer" || user?.global_role === "admin";
  const [templates, setTemplates] = useState<ChangeTemplate[]>([]);
  const [records, setRecords] = useState<ChangeRecord[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [pending, setPending] = useState<Workflow[]>([]);
  const [review, setReview] = useState<ReviewStatus | null>(null);
  const [policy, setPolicy] = useState<ValidationPolicy | null>(null);

  const refresh = () => {
    ChangeApi.templates().then(setTemplates).catch(() => undefined);
    ChangeApi.records().then(setRecords).catch(() => undefined);
    Schedules.list().then(setSchedules).catch(() => undefined);
    Canvas.list().then(setWorkflows).catch(() => undefined);
    Validation.reviewStatus().then(setReview).catch(() => undefined);
    Validation.policy().then(setPolicy).catch(() => undefined);
    if (canReview) Canvas.pendingReviews().then(setPending).catch(() => setPending([]));
  };
  useEffect(refresh, [canReview]);

  function decide(id: string, decision: string) {
    Canvas.review(id, decision).then(refresh).catch(() => undefined);
  }

  return (
    <Page title="Governance" subtitle="Change control, scheduling, review & lifecycle validation">
      {review && (
        <Card style={{ marginBottom: 14 }}>
          <SectionTitle>Automation review &amp; pruning</SectionTitle>
          <div style={{ display: "flex", gap: 24, marginBottom: 10 }}>
            <Stat label="Fresh" value={review.fresh} color="var(--color-ok)" />
            <Stat label="Stale" value={review.stale} color="var(--color-warn)" />
            <Stat label="Never reviewed" value={review.never_reviewed} color="var(--color-danger)" />
            <Stat label="Total" value={review.total} />
            {policy && (
              <div style={{ marginLeft: "auto", alignSelf: "center", fontSize: "0.72rem", color: "var(--text-muted)" }}>
                review SLA: {policy.max_review_age_days}d · CMDB checks {policy.enforce_cmdb_consistency ? "on" : "off"}
              </div>
            )}
          </div>
          {review.oldest.length > 0 && (
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
              Oldest reviewed: {review.oldest.slice(0, 5).map((o) => o.name).join(" · ")}
            </div>
          )}
        </Card>
      )}
      {canReview && (
        <Card style={{ marginBottom: 14 }}>
          <SectionTitle>Workflow review inbox</SectionTitle>
          {pending.length === 0 && <Empty>No workflows awaiting review.</Empty>}
          {pending.map((w) => (
            <Row key={w.id}>
              <span>
                {w.name}{" "}
                <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
                  by {w.submitted_by ?? "?"} · {w.review_state}
                </span>
              </span>
              <span style={{ display: "flex", gap: 6 }}>
                <Button onClick={() => decide(w.id, "approve")}>Approve</Button>
                <Button variant="ghost" onClick={() => decide(w.id, "request_changes")}>Changes</Button>
                <Button variant="ghost" onClick={() => decide(w.id, "reject")}>Reject</Button>
              </span>
            </Row>
          ))}
        </Card>
      )}
      <div style={{ marginBottom: 14 }}>
        <ChangeCalendar />
      </div>

      {user?.global_role === "admin" && policy && (
        <div style={{ marginBottom: 14 }}>
          <ValidationPolicyEditor policy={policy} onSaved={setPolicy} />
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Card>
          <SectionTitle>Change templates</SectionTitle>
          <NewTemplate onCreated={refresh} />
          {templates.map((t) => (
            <Row key={t.id}>
              <span>{t.name}</span>
              <span style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>
                {t.risk}
                {t.cab_required ? " · CAB" : ""}
              </span>
            </Row>
          ))}
          {templates.length === 0 && <Empty>No change templates.</Empty>}
        </Card>

        <Card>
          <SectionTitle>Schedules</SectionTitle>
          <NewSchedule workflows={workflows} onCreated={refresh} />
          {schedules.map((s) => (
            <Row key={s.id}>
              <span>{s.name}</span>
              <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                  {s.kind === "interval" ? `every ${s.interval_seconds}s` : `daily ${s.daily_time}`}
                </span>
                <Button variant="ghost" onClick={() => Schedules.runNow(s.id).then(refresh)}>Run</Button>
                <Button variant="ghost" onClick={() => Schedules.remove(s.id).then(refresh)}>✕</Button>
              </span>
            </Row>
          ))}
          {schedules.length === 0 && <Empty>No schedules.</Empty>}
        </Card>
      </div>

      <Card style={{ marginTop: 14 }}>
        <SectionTitle>Change records</SectionTitle>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.84rem" }}>
          <tbody>
            {records.map((r) => (
              <tr key={r.number} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ padding: "8px 6px", fontFamily: "ui-monospace, monospace" }}>{r.number}</td>
                <td style={{ padding: "8px 6px" }}>{r.short_description}</td>
                <td style={{ padding: "8px 6px", color: "var(--text-muted)" }}>{r.risk}</td>
                <td style={{ padding: "8px 6px", textAlign: "right" }}><StatusBadge status={r.state} /></td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr><td style={{ padding: "10px 6px", color: "var(--text-muted)" }}>No change records yet.</td></tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: color ?? "var(--text)" }}>{value}</div>
      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{label}</div>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>
      {children}
    </h2>
  );
}
function Row({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderTop: "1px solid var(--border)" }}>
      {children}
    </div>
  );
}
function Empty({ children }: { children: React.ReactNode }) {
  return <div style={{ color: "var(--text-muted)", fontSize: "0.82rem", padding: "8px 0" }}>{children}</div>;
}

function NewTemplate({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [cab, setCab] = useState(false);
  return (
    <div style={{ display: "flex", gap: 8, margin: "8px 0" }}>
      <input placeholder="Template name" value={name} onChange={(e) => setName(e.target.value)} style={field} />
      <label style={{ display: "flex", gap: 4, alignItems: "center", fontSize: "0.78rem" }}>
        <input type="checkbox" checked={cab} onChange={(e) => setCab(e.target.checked)} /> CAB
      </label>
      <Button
        onClick={() => {
          if (!name) return;
          ChangeApi.createTemplate({ name, cab_required: cab, risk: cab ? "high" : "low" }).then(() => {
            setName("");
            onCreated();
          });
        }}
      >
        Add
      </Button>
    </div>
  );
}

function NewSchedule({ workflows, onCreated }: { workflows: Workflow[]; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [wf, setWf] = useState("");
  const [interval, setInterval] = useState(3600);
  return (
    <div style={{ display: "flex", gap: 8, margin: "8px 0", flexWrap: "wrap" }}>
      <input placeholder="Schedule name" value={name} onChange={(e) => setName(e.target.value)} style={field} />
      <select value={wf} onChange={(e) => setWf(e.target.value)} style={field}>
        <option value="">workflow…</option>
        {workflows.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
      </select>
      <input type="number" value={interval} onChange={(e) => setInterval(Number(e.target.value))} style={{ ...field, width: 90 }} />
      <Button
        onClick={() => {
          if (!name || !wf) return;
          Schedules.create({ name, workflow_id: wf, kind: "interval", interval_seconds: interval }).then(() => {
            setName("");
            onCreated();
          });
        }}
      >
        Add
      </Button>
    </div>
  );
}

const field: React.CSSProperties = {
  flex: 1,
  minWidth: 100,
  padding: "7px 9px",
  borderRadius: 7,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
};

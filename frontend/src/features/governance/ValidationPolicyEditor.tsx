// Admin editor for the single lifecycle ValidationPolicy (J40) — the one gate every execution
// consults (ADR-0006). Admin-only; PUTs the full policy and reports the result.

import { useState } from "react";
import { Validation, type ValidationPolicy } from "@/shared/api/client";
import { Button, Card } from "@/shared/ui/primitives";

const TOGGLES: { key: keyof ValidationPolicy; label: string; help: string }[] = [
  { key: "enforce_cmdb_consistency", label: "Enforce CMDB consistency", help: "Validate targets against the CMDB before a run." },
  { key: "reject_retired", label: "Reject retired CIs", help: "Block automation targeting a retired CI." },
  { key: "reject_unknown_ci", label: "Reject unknown CIs", help: "Block targets not found in the CMDB." },
  { key: "block_destructive_on_cluster", label: "Block destructive on cluster members", help: "Refuse destructive actions on cluster-member datastores." },
];

export function ValidationPolicyEditor({ policy, onSaved }: { policy: ValidationPolicy; onSaved: (p: ValidationPolicy) => void }) {
  const [draft, setDraft] = useState<ValidationPolicy>(policy);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setMsg(null);
    try {
      const updated = await Validation.updatePolicy(draft);
      onSaved(updated);
      setMsg("Saved — applies to every execution.");
    } catch (e) {
      setMsg(e instanceof Error ? `Save failed: ${e.message}` : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <h2 style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>
        Lifecycle validation policy
      </h2>
      <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", margin: "0 0 10px" }}>
        The single gate every automation passes before it runs. Admin-only.
      </p>
      {TOGGLES.map((t) => (
        <label key={String(t.key)} style={{ display: "flex", gap: 8, alignItems: "flex-start", padding: "5px 0" }}>
          <input
            type="checkbox"
            checked={Boolean(draft[t.key])}
            onChange={(e) => setDraft({ ...draft, [t.key]: e.target.checked })}
          />
          <span>
            <div style={{ fontSize: "0.84rem" }}>{t.label}</div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{t.help}</div>
          </span>
        </label>
      ))}
      <label style={{ display: "flex", gap: 8, alignItems: "center", margin: "10px 0", fontSize: "0.84rem" }}>
        Max review age (days)
        <input
          type="number"
          min={1}
          value={draft.max_review_age_days}
          onChange={(e) => setDraft({ ...draft, max_review_age_days: Number(e.target.value) })}
          style={{ width: 80, padding: "5px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
        />
      </label>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 6 }}>
        <Button size="sm" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save policy"}</Button>
        {msg && <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{msg}</span>}
      </div>
    </Card>
  );
}

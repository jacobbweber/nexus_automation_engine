// Reviewer approvals queue (M26.6) — pending run/CI-change approvals; open the multi-audience
// packet and approve / reject / request changes with a comment.

import { useCallback, useEffect, useState } from "react";
import { ApiError, Review, type ApprovalRequest } from "@/shared/api/client";
import { Button, Card, Page } from "@/shared/ui/primitives";
import { ReviewPacketView } from "@/shared/ui/ReviewPacketView";

export function ApprovalsPage() {
  const [pending, setPending] = useState<ApprovalRequest[]>([]);
  const [selected, setSelected] = useState<ApprovalRequest | null>(null);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    Review.approvals().then(setPending).catch(() => setPending([]));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function decide(decision: string) {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      await Review.decide(selected.id, decision, comment);
      setSelected(null);
      setComment("");
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Decision failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Approvals" subtitle="Pending run & CI-change reviews">
      {error && (
        <div role="alert" style={{ color: "var(--danger)", marginBottom: 10, fontSize: "0.85rem" }}>
          {error}
        </div>
      )}
      <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
        <div style={{ width: 300, flexShrink: 0 }}>
          {pending.length === 0 ? (
            <Card>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", margin: 0 }}>
                No pending approvals. ✓
              </p>
            </Card>
          ) : (
            pending.map((a) => (
              <button
                key={a.id}
                onClick={() => {
                  setSelected(a);
                  setComment("");
                }}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "10px 12px",
                  marginBottom: 6,
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                  cursor: "pointer",
                  background: selected?.id === a.id ? "var(--accent-soft)" : "var(--surface)",
                  color: "var(--text)",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{a.title}</div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                  {a.change_class} · needs {a.required_level} · {a.source_type}
                </div>
              </button>
            ))
          )}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          {selected ? (
            <Card>
              {selected.packet ? (
                <ReviewPacketView packet={selected.packet} />
              ) : (
                <div style={{ fontSize: "0.85rem" }}>
                  <strong>{selected.title}</strong>
                  <p style={{ color: "var(--text-muted)" }}>{selected.comment}</p>
                </div>
              )}
              <div style={{ marginTop: 14, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
                <input
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Comment (optional)"
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    background: "var(--bg)",
                    color: "var(--text)",
                    marginBottom: 10,
                    boxSizing: "border-box",
                  }}
                />
                <div style={{ display: "flex", gap: 8 }}>
                  <Button onClick={() => decide("approve")} disabled={busy}>
                    Approve
                  </Button>
                  <Button variant="ghost" onClick={() => decide("request_changes")} disabled={busy}>
                    Request changes
                  </Button>
                  <Button variant="ghost" onClick={() => decide("reject")} disabled={busy}>
                    Reject
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <Card>
              <p style={{ color: "var(--text-muted)" }}>Select a pending item to review.</p>
            </Card>
          )}
        </div>
      </div>
    </Page>
  );
}

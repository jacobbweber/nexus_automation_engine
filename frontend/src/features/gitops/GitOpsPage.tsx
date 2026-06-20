// GitOps admin surface (M28.5) — config-as-code status, on-demand backup, commit history with a
// diff view, and the pull-preview (repo vs live). Local git only; admins can back up.

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  type GitCommit,
  GitOps,
  type PullPreview,
  type RepoStatus,
} from "@/shared/api/client";
import { useAuth } from "@/app/auth";
import { Button, Card, Page } from "@/shared/ui/primitives";

export function GitOpsPage() {
  const { user } = useAuth();
  const isAdmin = user?.global_role === "admin";
  const [status, setStatus] = useState<RepoStatus | null>(null);
  const [history, setHistory] = useState<GitCommit[]>([]);
  const [preview, setPreview] = useState<PullPreview | null>(null);
  const [diff, setDiff] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    GitOps.status().then(setStatus).catch(() => setStatus(null));
    GitOps.history().then(setHistory).catch(() => setHistory([]));
    GitOps.pullPreview().then(setPreview).catch(() => setPreview(null));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function backup() {
    setBusy(true);
    setError(null);
    try {
      await GitOps.sync();
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Backup failed.");
    } finally {
      setBusy(false);
    }
  }

  async function showDiff(c: GitCommit) {
    // diff the whole tree for this commit against its parent
    const res = await GitOps.diff(".", `${c.sha}~1`, c.sha).catch(() => ({ diff: "" }));
    setDiff(res.diff || "(no textual diff)");
  }

  return (
    <Page title="GitOps — config as code" subtitle="Version, back up & restore the platform's configuration">
      {error && (
        <div role="alert" style={{ color: "var(--danger)", marginBottom: 10, fontSize: "0.85rem" }}>
          {error}
        </div>
      )}

      <Card style={{ marginBottom: 14 }}>
        <SectionTitle>Repository</SectionTitle>
        {!status?.available ? (
          <p style={{ color: "var(--text-muted)", margin: 0 }}>
            Versioning backend unavailable (git not present, or no repo yet).
          </p>
        ) : (
          <div style={{ display: "flex", gap: 18, flexWrap: "wrap", alignItems: "center" }}>
            <Stat label="Commits" value={String(status.commits)} />
            <Stat label="HEAD" value={status.head ?? "—"} />
            <Stat label="State" value={status.dirty ? "uncommitted changes" : "clean"} accent={status.dirty ? "var(--warn)" : "var(--success)"} />
            <span style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>{status.path}</span>
            {isAdmin && (
              <span style={{ marginLeft: "auto" }}>
                <Button onClick={backup} disabled={busy}>{busy ? "Backing up…" : "Back up now"}</Button>
              </span>
            )}
          </div>
        )}
      </Card>

      {preview && (
        <Card style={{ marginBottom: 14 }}>
          <SectionTitle>Pull preview (repo vs live)</SectionTitle>
          {preview.in_sync ? (
            <p style={{ color: "var(--success)", margin: 0, fontSize: "0.85rem" }}>
              ✓ Live config matches the committed config.
            </p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: "0.82rem" }}>
              {preview.differences.map((d) => (
                <li key={d.path}>
                  <span style={{ color: "var(--warn)" }}>{d.change}</span> · {d.path}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
        <Card style={{ flex: 1, minWidth: 0 }}>
          <SectionTitle>History</SectionTitle>
          {history.length === 0 ? (
            <p style={{ color: "var(--text-muted)", margin: 0, fontSize: "0.85rem" }}>No commits yet.</p>
          ) : (
            history.map((c) => (
              <button
                key={c.sha}
                onClick={() => showDiff(c)}
                style={{
                  display: "block", width: "100%", textAlign: "left", padding: "7px 10px",
                  marginBottom: 4, borderRadius: 8, border: "1px solid var(--border)",
                  cursor: "pointer", background: "var(--surface)", color: "var(--text)",
                }}
              >
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{c.sha}</span>{" "}
                <span style={{ fontSize: "0.82rem" }}>{c.message.split("\n")[0]}</span>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                  {c.author} · {new Date(c.date).toLocaleString()}
                </div>
              </button>
            ))
          )}
        </Card>
        <Card style={{ flex: 1, minWidth: 0 }}>
          <SectionTitle>Diff</SectionTitle>
          <pre style={{ margin: 0, fontSize: "0.72rem", overflow: "auto", maxHeight: 360, whiteSpace: "pre-wrap" }}>
            {diff ?? "Select a commit to view its diff."}
          </pre>
        </Card>
      </div>
    </Page>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div>
      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{label}</div>
      <div style={{ fontSize: "1rem", fontWeight: 600, color: accent ?? "var(--text)" }}>{value}</div>
    </div>
  );
}
function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1, marginTop: 0 }}>
      {children}
    </h2>
  );
}

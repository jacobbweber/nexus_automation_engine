// Calm, reusable empty state — kills blank-page paralysis with a clear title, optional helper
// text, and a single primary action (often a "set this up for me" shortcut).

import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div
      role="status"
      style={{
        textAlign: "center",
        padding: "var(--space-7) var(--space-5)",
        color: "var(--text-muted)",
      }}
    >
      <div style={{ opacity: 0.55, marginBottom: "var(--space-3)", display: "flex", justifyContent: "center" }}>
        {icon ?? <Inbox size={32} />}
      </div>
      <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text)" }}>{title}</div>
      {description && (
        <p style={{ maxWidth: "44ch", margin: "var(--space-2) auto 0", fontSize: "0.85rem", lineHeight: 1.5 }}>
          {description}
        </p>
      )}
      {action && <div style={{ marginTop: "var(--space-4)" }}>{action}</div>}
    </div>
  );
}

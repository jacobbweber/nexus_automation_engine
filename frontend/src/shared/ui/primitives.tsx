import type { CSSProperties, ReactNode } from "react";

export function Page({ title, subtitle, actions, children }: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div style={{ padding: 28 }}>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: "1.35rem", fontWeight: 700, margin: 0 }}>{title}</h1>
          {subtitle && (
            <p style={{ color: "var(--text-muted)", margin: "4px 0 0", fontSize: "0.9rem" }}>
              {subtitle}
            </p>
          )}
        </div>
        <div style={{ marginLeft: "auto" }}>{actions}</div>
      </div>
      {children}
    </div>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: 12,
        background: "var(--surface)",
        padding: 18,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  SUCCESS: "var(--color-ok)",
  completed: "var(--color-ok)",
  RUNNING: "var(--color-accent)",
  running: "var(--color-accent)",
  PENDING: "var(--color-warn)",
  FAILED: "var(--color-danger)",
  failed: "var(--color-danger)",
  CANCELLED: "var(--text-muted)",
  approved: "var(--color-ok)",
  draft: "var(--text-muted)",
};

export function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "var(--text-muted)";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: "0.75rem",
        color,
        fontWeight: 600,
      }}
    >
      <span style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />
      {status}
    </span>
  );
}

export function Button({ children, onClick, variant = "primary", disabled, type }: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost";
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  const primary = variant === "primary";
  return (
    <button
      type={type ?? "button"}
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: "8px 14px",
        borderRadius: 8,
        border: primary ? "none" : "1px solid var(--border)",
        background: primary ? "var(--color-accent)" : "transparent",
        color: primary ? "#fff" : "var(--text)",
        fontWeight: 600,
        fontSize: "0.85rem",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
      }}
    >
      {children}
    </button>
  );
}

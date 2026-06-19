import {
  Ban,
  BadgeCheck,
  CheckCircle2,
  Circle,
  Clock,
  Loader2,
  MinusCircle,
  Pencil,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import type { CSSProperties, ReactNode } from "react";

export function Page({ title, subtitle, actions, children }: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div style={{ padding: "var(--space-6)" }}>
      <div style={{ display: "flex", alignItems: "center", marginBottom: "var(--space-5)" }}>
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
        borderRadius: "var(--radius-lg)",
        background: "var(--surface)",
        boxShadow: "var(--shadow-1)",
        padding: "var(--space-5)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

// --- Protected Run/Status badge -------------------------------------------------------------
// Status is conveyed by an ICON (shape) as well as color, so it is never color-only — the
// accessibility guarantee for protected operational status (ADR-0007, design-system §7.1).
// Colors resolve through the --run-* / status contract, so they honor mode/area/theme.

interface StatusStyle {
  color: string;
  icon: LucideIcon;
  spin?: boolean;
}
const STATUS: Record<string, StatusStyle> = {
  running: { color: "var(--run-running)", icon: Loader2, spin: true },
  completed: { color: "var(--run-ok)", icon: CheckCircle2 },
  success: { color: "var(--run-ok)", icon: CheckCircle2 },
  failed: { color: "var(--run-failed)", icon: XCircle },
  pending: { color: "var(--run-warn)", icon: Clock },
  skipped: { color: "var(--run-skipped)", icon: MinusCircle },
  cancelled: { color: "var(--text-muted)", icon: Ban },
  // review / change lifecycle states
  draft: { color: "var(--text-muted)", icon: Circle },
  submitted: { color: "var(--warn)", icon: Clock },
  in_review: { color: "var(--warn)", icon: Clock },
  changes_requested: { color: "var(--warn)", icon: Pencil },
  approved: { color: "var(--success)", icon: CheckCircle2 },
  published: { color: "var(--success)", icon: BadgeCheck },
  rejected: { color: "var(--danger)", icon: XCircle },
  scheduled: { color: "var(--info)", icon: Clock },
  implement: { color: "var(--info)", icon: Clock },
};

export function StatusBadge({ status, size = "sm" }: { status: string; size?: "sm" | "md" }) {
  const key = String(status).toLowerCase();
  const s = STATUS[key] ?? { color: "var(--text-muted)", icon: Circle };
  const Icon = s.icon;
  const px = size === "md" ? 15 : 13;
  // Label uses --text (always AA); the colored icon (a graphic) carries the status hue, so the
  // badge is legible and never relies on color alone (design-system §7.1, A7 contrast gate).
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "2px 8px",
        borderRadius: "var(--radius-pill)",
        background: `color-mix(in srgb, ${s.color} 12%, transparent)`,
        fontSize: size === "md" ? "0.82rem" : "0.75rem",
        color: "var(--text)",
        fontWeight: 600,
      }}
    >
      <span style={{ color: s.color, display: "inline-flex" }}>
        <Icon size={px} className={s.spin ? "nx-spin" : undefined} aria-hidden />
      </span>
      <span style={{ textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</span>
    </span>
  );
}

// --- Button ---------------------------------------------------------------------------------

type ButtonVariant = "primary" | "ghost" | "soft" | "danger" | "quiet";

const VARIANT: Record<ButtonVariant, CSSProperties> = {
  primary: {
    background: "var(--area-accent, var(--accent))",
    color: "var(--area-accent-contrast, var(--accent-contrast))",
    border: "1px solid transparent",
  },
  soft: { background: "var(--accent-soft)", color: "var(--accent)", border: "1px solid transparent" },
  ghost: { background: "transparent", color: "var(--text)", border: "1px solid var(--border)" },
  quiet: { background: "transparent", color: "var(--text-muted)", border: "1px solid transparent" },
  danger: { background: "var(--danger)", color: "#fff", border: "1px solid transparent" },
};

export function Button({ children, onClick, variant = "primary", disabled, type, size = "md", title }: {
  children: ReactNode;
  onClick?: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  type?: "button" | "submit";
  size?: "sm" | "md";
  title?: string;
}) {
  return (
    <button
      type={type ?? "button"}
      onClick={onClick}
      disabled={disabled}
      title={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        minHeight: size === "sm" ? 36 : 44,
        padding: size === "sm" ? "6px 12px" : "9px 16px",
        borderRadius: "var(--radius-md)",
        fontWeight: 600,
        fontSize: "0.85rem",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.55 : 1,
        transition: "background-color var(--dur-1) var(--ease-out)",
        ...VARIANT[variant],
      }}
    >
      {children}
    </button>
  );
}

import { Workflow } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/auth";

export function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("operator");
  const [password, setPassword] = useState("operator123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) navigate("/", { replace: true });
  }, [user, navigate]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch {
      setError("Invalid username or password");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "grid", placeItems: "center", height: "100%" }}>
      <form
        onSubmit={submit}
        style={{
          width: 340,
          padding: 28,
          border: "1px solid var(--border)",
          borderRadius: 14,
          background: "var(--surface)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
          <Workflow size={24} color="var(--color-accent)" />
          <span style={{ fontWeight: 700, fontSize: "1.1rem", letterSpacing: 1 }}>NEXUS</span>
        </div>
        <Field label="Username" value={username} onChange={setUsername} />
        <Field label="Password" type="password" value={password} onChange={setPassword} />
        {error && <div style={{ color: "var(--color-danger)", fontSize: "0.85rem" }}>{error}</div>}
        <button
          type="submit"
          disabled={busy}
          style={{
            width: "100%",
            marginTop: 14,
            padding: "10px",
            borderRadius: 8,
            border: "none",
            background: "var(--color-accent)",
            color: "#fff",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <div style={{ marginTop: 14, fontSize: "0.72rem", color: "var(--text-muted)" }}>
          Demo users: admin / engineer / operator / consumer (password = name + "123").
        </div>
      </form>
    </div>
  );
}

function Field(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label style={{ display: "block", marginBottom: 12 }}>
      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{props.label}</span>
      <input
        type={props.type ?? "text"}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        style={{
          width: "100%",
          marginTop: 4,
          padding: "9px 10px",
          borderRadius: 8,
          border: "1px solid var(--border)",
          background: "var(--bg)",
          color: "var(--text)",
          boxSizing: "border-box",
        }}
      />
    </label>
  );
}

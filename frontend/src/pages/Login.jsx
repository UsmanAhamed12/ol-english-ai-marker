import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AlertCircle, Loader2 } from "lucide-react";
import AuthShell from "./../components/common/AuthShell.jsx";
import { useAuth } from "./../hooks/useAuth.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate(location.state?.from || "/papers", { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Sign in"
      subtitle="Your papers and knowledge base stay on this machine."
      footer={
        <span>
          New here?{" "}
          <Link to="/register" className="font-medium text-ink underline underline-offset-4">
            Create an account
          </Link>
        </span>
      }
    >
      <form onSubmit={submit} className="space-y-3" noValidate>
        <div>
          <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="field"
            placeholder="teacher@example.com"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="field"
            placeholder="••••••••"
          />
        </div>

        {error ? (
          <p className="flex items-start gap-2 rounded-lg border border-red/40 bg-redWash px-3 py-2 text-xs text-red">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {error}
          </p>
        ) : null}

        <button type="submit" className="ink-btn w-full" disabled={busy}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthShell>
  );
}
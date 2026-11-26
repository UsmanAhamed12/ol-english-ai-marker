import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, Loader2 } from "lucide-react";
import AuthShell from "./../components/common/AuthShell.jsx";
import { useAuth } from "./../hooks/useAuth.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }

    setBusy(true);
    try {
      await register({ email: email.trim(), password, full_name: fullName.trim() });
      navigate("/papers", { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="One account per teacher. Your papers are visible only to you."
      footer={
        <span>
          Already have one?{" "}
          <Link to="/login" className="font-medium text-ink underline underline-offset-4">
            Sign in
          </Link>
        </span>
      }
    >
      <form onSubmit={submit} className="space-y-3" noValidate>
        <div>
          <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="full_name">
            Full name
          </label>
          <input
            id="full_name"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            className="field"
            placeholder="A. Perera"
            autoComplete="name"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="field"
            placeholder="teacher@example.com"
            autoComplete="email"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="field"
            placeholder="At least 8 characters, a letter and a number"
            autoComplete="new-password"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="confirm">
            Confirm password
          </label>
          <input
            id="confirm"
            type="password"
            required
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
            className="field"
            placeholder="Repeat the password"
            autoComplete="new-password"
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
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}
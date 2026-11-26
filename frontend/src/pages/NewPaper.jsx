import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, ArrowLeft, Loader2, Sparkles } from "lucide-react";
import FileDrop from "./../components/common/FileDrop.jsx";
import { api } from "./../api/api.js";

export default function NewPaper() {
  const navigate = useNavigate();

  const [script, setScript] = useState([]);
  const [scheme, setScheme] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const ready = script.length > 0 && scheme.length > 0;

  const start = async () => {
    if (!script.length) {
      setError("Add the student's answer script.");
      return;
    }
    if (!scheme.length) {
      setError("Add the marking scheme for this paper.");
      return;
    }

    setError("");
    setBusy(true);
    try {
      const paper = await api.createPaper({ script, scheme });
      navigate(`/papers/${paper.id}`);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <>
      <Link to="/papers" className="inline-flex items-center gap-1.5 text-xs text-inkSoft hover:text-ink">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to papers
      </Link>

      <div className="mt-5">
        <p className="eyebrow">New marking</p>
        <h1 className="display mt-2 text-4xl font-medium leading-tight">Mark a paper</h1>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-inkSoft">
          Upload the student's full paper and the marking scheme. That's all — no details to fill in.
        </p>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-medium text-inkSoft">1 · Student paper</p>
          <FileDrop
            label="Unmarked answer script"
            hint="Full paper · PDF, JPG, PNG · up to 6 files"
            files={script}
            onChange={setScript}
          />
        </div>

        <div>
          <p className="mb-2 text-xs font-medium text-inkSoft">2 · Marking scheme</p>
          <FileDrop
            label="Scheme or rubric"
            hint="The answer key for this paper · PDF, JPG, PNG"
            files={scheme}
            onChange={setScheme}
            limit={3}
          />
        </div>
      </div>

      <section className="paper-card mt-6 p-5 sm:p-6">
        {error ? (
          <p className="mb-4 flex items-start gap-2 rounded-lg border border-red/40 bg-redWash px-3 py-2.5 text-xs text-red">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {error}
          </p>
        ) : null}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs italic text-inkSoft">
            {ready
              ? `${script.length} script file${script.length > 1 ? "s" : ""} · ${scheme.length} scheme file${
                  scheme.length > 1 ? "s" : ""
                } — ready to mark.`
              : "Add the student's paper and the marking scheme to start."}
          </p>

          <button type="button" className="ink-btn" disabled={busy} onClick={start}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {busy ? "Uploading…" : "Extract & mark paper"}
          </button>
        </div>

        <p className="mt-3 border-t border-line pt-3 text-[0.72rem] leading-relaxed text-inkSoft">
          A full paper usually takes one to three minutes to read and mark. You can leave the page —
          marking continues on the server, and the paper shows its progress when you open it.
        </p>
      </section>
    </>
  );
}
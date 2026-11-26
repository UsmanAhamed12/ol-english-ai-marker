import { useCallback, useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Database, Loader2, Sparkles, Trash2, Upload } from "lucide-react";
import FileDrop from "./../components/common/FileDrop.jsx";
import { api } from "./../api/api.js";
import { formatDate } from "./../utils/format.js";

const KINDS = ["Syllabus", "Past paper", "Marking scheme", "Guidance"];

export default function Knowledge() {
  const [sources, setSources] = useState([]);
  const [stats, setStats] = useState(null);
  const [files, setFiles] = useState([]);
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("Syllabus");
  const [year, setYear] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [list, counts] = await Promise.all([api.knowledge(), api.knowledgeStats()]);
    setSources(list || []);
    setStats(counts);
  }, []);

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, [refresh]);

  const upload = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!files.length) {
      setError("Choose a document to add.");
      return;
    }
    if (title.trim().length < 2) {
      setError("Give the document a title.");
      return;
    }

    setBusy(true);
    try {
      const created = await api.uploadKnowledge({
        file: files[0],
        title: title.trim(),
        kind,
        year: year.trim(),
        notes: notes.trim(),
      });
      setMessage(`“${created.title}” indexed into ${created.chunk_count} chunks.`);
      setFiles([]);
      setTitle("");
      setYear("");
      setNotes("");
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const indexPapers = async () => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await api.indexPapers();
      setMessage(`${result.papers} marked paper(s) added as worked examples.`);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (source) => {
    if (!window.confirm(`Remove “${source.title}” from the knowledge base?`)) return;
    try {
      await api.deleteKnowledge(source.id);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Knowledge base</p>
          <h1 className="display mt-2 text-4xl font-medium leading-tight">What the marker studies</h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-inkSoft">
            Syllabus, past papers and marked examples are chunked and indexed locally. The most
            relevant chunks are handed to the marker with every paper — no extra service, no cost.
          </p>
        </div>

        <button type="button" className="ghost-btn" onClick={indexPapers} disabled={busy}>
          <Sparkles className="h-4 w-4" /> Index my marked papers
        </button>
      </div>

      {stats ? (
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {[
            { label: "Chunks indexed", value: stats.vectors },
            { label: "Knowledge chunks", value: stats.knowledge_chunks },
            { label: "Example chunks", value: stats.example_chunks },
          ].map((item) => (
            <div key={item.label} className="paper-card p-4">
              <p className="eyebrow !text-[0.55rem]">{item.label}</p>
              <p className="display mt-1 text-2xl font-medium">{item.value}</p>
            </div>
          ))}
        </div>
      ) : null}

      {message ? (
        <p className="mt-4 flex items-start gap-2 rounded-xl border border-sage/40 bg-sageWash px-4 py-3 text-sm text-sage">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          {message}
        </p>
      ) : null}

      {error ? (
        <p className="mt-4 flex items-start gap-2 rounded-xl border border-red/40 bg-redWash px-4 py-3 text-sm text-red">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : null}

      <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_1.15fr]">
        <form onSubmit={upload} className="paper-card p-5 sm:p-6">
          <p className="text-sm font-medium">Add a document</p>
          <p className="mt-1 text-xs text-inkSoft">
            PDF or photograph of a syllabus, past paper or scheme.
          </p>

          <div className="mt-4">
            <FileDrop
              label="Document"
              hint="PDF, JPG or PNG · one file"
              files={files}
              onChange={setFiles}
              multiple={false}
            />
          </div>

          <div className="mt-4 space-y-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="title">
                Title
              </label>
              <input
                id="title"
                className="field"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="O/L English syllabus 2024"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="kind">
                  Type
                </label>
                <select
                  id="kind"
                  className="field"
                  value={kind}
                  onChange={(event) => setKind(event.target.value)}
                >
                  {KINDS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="year">
                  Year
                </label>
                <input
                  id="year"
                  className="field"
                  value={year}
                  onChange={(event) => setYear(event.target.value)}
                  placeholder="2024"
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-inkSoft" htmlFor="notes">
                Notes
              </label>
              <input
                id="notes"
                className="field"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Optional"
              />
            </div>
          </div>

          <button type="submit" className="ink-btn mt-4 w-full" disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {busy ? "Reading and indexing…" : "Add to knowledge base"}
          </button>
        </form>

        <section>
          <p className="text-sm font-medium">Indexed documents</p>

          {sources.length ? (
            <ul className="mt-3 space-y-2">
              {sources.map((source) => (
                <li
                  key={source.id}
                  className="flex items-start gap-3 rounded-xl border border-line bg-white px-4 py-3"
                >
                  <Database className="mt-0.5 h-4 w-4 shrink-0 text-inkSoft" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{source.title}</p>
                    <p className="mt-0.5 text-xs text-inkSoft">
                      {source.kind}
                      {source.year ? ` · ${source.year}` : ""} · {source.chunk_count} chunks ·{" "}
                      {formatDate(source.created_at)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => remove(source)}
                    className="text-inkSoft transition hover:text-red"
                    aria-label={`Remove ${source.title}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 rounded-xl border border-dashed border-line px-4 py-10 text-center text-sm italic text-inkSoft">
              Nothing indexed yet. Add the syllabus first — it sharpens every mark.
            </p>
          )}
        </section>
      </div>
    </>
  );
}
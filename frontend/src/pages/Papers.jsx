import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, ArrowRight, FilePlus2 } from "lucide-react";
import StatusPill from "./../components/common/StatusPill.jsx";
import { api } from "./../api/api.js";
import { fmt, formatDate } from "./../utils/format.js";

export default function Papers() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;

    api
      .papers()
      .then((items) => {
        if (alive) setPapers(items || []);
      })
      .catch((err) => {
        if (alive) setError(err.message);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Marked papers</p>
          <h1 className="display mt-2 text-4xl font-medium leading-tight">Your marking studio</h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-inkSoft">
            Upload a script with its scheme, and every test is marked against the answer key with
            feedback, tips and the skill behind each lost mark.
          </p>
        </div>

        <Link to="/new" className="ink-btn">
          <FilePlus2 className="h-4 w-4" /> New marking
        </Link>
      </div>

      {error ? (
        <p className="mt-6 flex items-start gap-2 rounded-xl border border-red/40 bg-redWash px-4 py-3 text-sm text-red">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : null}

      {loading ? (
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {[0, 1, 2, 3].map((key) => (
            <div key={key} className="h-28 animate-pulse rounded-2xl bg-paperDeep" />
          ))}
        </div>
      ) : papers.length ? (
        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {papers.map((paper) => (
            <li key={paper.id}>
              <Link
                to={`/papers/${paper.id}`}
                className="paper-card group flex h-full flex-col justify-between p-5 transition hover:border-ink/30 hover:bg-white"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{paper.student_name || "Untitled script"}</p>
                    <p className="mt-0.5 text-xs text-inkSoft">
                      {paper.paper_type || "Full paper"} · {formatDate(paper.created_at)}
                    </p>
                  </div>
                  <StatusPill status={paper.status} />
                </div>

                <div className="mt-4 flex items-end justify-between">
                  <p className="display text-2xl font-medium">
                    {paper.status === "marked" || paper.status === "review"
                      ? `${fmt(paper.normalized_score)}`
                      : "—"}
                    <span className="text-xs text-inkSoft"> / 100</span>
                  </p>
                  <span className="inline-flex items-center gap-1 text-[0.72rem] text-inkSoft transition group-hover:text-ink">
                    Open <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <div className="paper-card mt-6 px-6 py-14 text-center">
          <p className="display text-2xl font-medium">No papers marked yet</p>
          <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-inkSoft">
            Add the student's script and the marking scheme — nothing else to fill in.
          </p>
          <Link to="/new" className="ink-btn mt-5">
            <FilePlus2 className="h-4 w-4" /> Mark a paper
          </Link>
        </div>
      )}
    </>
  );
}
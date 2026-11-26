import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertCircle, ArrowLeft, Loader2, Printer, RefreshCw, Trash2 } from "lucide-react";
import QuestionRow from "./../components/marking/QuestionRow.jsx";
import StatusPill from "./../components/common/StatusPill.jsx";
import { api } from "./../api/api.js";
import { fmt, formatDate } from "./../utils/format.js";

const BUSY = ["extracting", "extracted", "marking"];

const PROGRESS = {
  extracting: "Reading handwriting and printed text",
  extracted: "Script read — preparing the questions",
  marking: "Marking every test against the scheme",
};

export default function PaperDetail() {
  const { paperId } = useParams();
  const navigate = useNavigate();

  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);

  const load = useCallback(async () => {
    const record = await api.paper(paperId);
    setPaper(record);
    return record;
  }, [paperId]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    load()
      .catch((err) => {
        if (alive) setError(err.message);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [load]);

  const busy = paper ? BUSY.includes(paper.status) : false;

  useEffect(() => {
    if (!busy) return undefined;
    const timer = setInterval(() => {
      load().catch(() => {});
    }, 4000);
    return () => clearInterval(timer);
  }, [busy, load]);

  const remark = async () => {
    setWorking(true);
    setError("");
    try {
      await api.remark(paperId);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setWorking(false);
    }
  };

  const remove = async () => {
    if (!window.confirm("Delete this paper with its marks and uploaded files?")) return;
    try {
      await api.deletePaper(paperId);
      navigate("/papers", { replace: true });
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div>
        <div className="h-8 w-40 animate-pulse rounded bg-paperDeep" />
        <div className="mt-6 h-52 animate-pulse rounded-2xl bg-paperDeep" />
        <div className="mt-4 h-40 animate-pulse rounded-2xl bg-paperDeep" />
      </div>
    );
  }

  if (error && !paper) {
    return (
      <div className="paper-card px-6 py-14 text-center">
        <p className="display text-2xl font-medium">This paper isn't here</p>
        <p className="mt-2 text-sm text-inkSoft">{error}</p>
        <Link to="/papers" className="ink-btn mt-5">
          Back to papers
        </Link>
      </div>
    );
  }

  const failed = paper.status === "failed";
  const score = paper.normalized_score ?? 0;
  const accuracy = paper.accuracy ? Math.round(paper.accuracy) : null;

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/papers" className="inline-flex items-center gap-1.5 text-xs text-inkSoft hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" /> All papers
          </Link>
          <h1 className="display mt-3 text-4xl font-medium leading-tight">
            {paper.student_name || "Untitled script"}
          </h1>
          <p className="mt-1 text-xs text-inkSoft">
            {paper.paper_title || "O/L English"} · {paper.paper_type || "Full paper"} ·{" "}
            {formatDate(paper.marked_at || paper.created_at)}
          </p>
        </div>

        <div className="no-print flex items-center gap-2">
          <StatusPill status={paper.status} />
          <button type="button" className="ghost-btn !px-3" onClick={() => window.print()}>
            <Printer className="h-3.5 w-3.5" /> Print
          </button>
          <button
            type="button"
            className="ghost-btn !px-3"
            onClick={remark}
            disabled={working || busy}
            title="Mark again"
          >
            {working ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
          </button>
          <button
            type="button"
            className="ghost-btn !px-3 !text-red"
            onClick={remove}
            title="Delete paper"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {error ? (
        <p className="mt-4 flex items-start gap-2 rounded-xl border border-red/40 bg-redWash px-4 py-3 text-sm text-red">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : null}

      {busy ? (
        <section className="paper-card mt-6 flex items-center gap-4 p-6">
          <Loader2 className="h-5 w-5 shrink-0 animate-spin text-red" />
          <div>
            <p className="text-sm font-medium">{PROGRESS[paper.status] || "Working on this paper…"}</p>
            <p className="mt-1 text-xs text-inkSoft">
              This page updates itself. A full paper usually takes one to three minutes.
            </p>
          </div>
        </section>
      ) : null}

      {failed ? (
        <section className="mt-6 rounded-xl border border-red/40 bg-redWash p-4 text-sm text-red">
          <p className="font-medium">This paper didn't finish marking.</p>
          <p className="mt-1">{paper.error_message || "The files could not be read."}</p>
          <p className="mt-2 text-xs">
            Check that the scan is clear and upright, then press the refresh button at the top.
          </p>
        </section>
      ) : null}

      <section className="paper-card mt-6 grid gap-6 p-6 sm:grid-cols-[auto_1fr] sm:gap-9 sm:p-8">
        <div className="sm:border-r sm:border-line sm:pr-9">
          <p className="eyebrow !text-[0.6rem]">Final score</p>
          <div className="mt-2 flex items-end gap-1">
            <span className="display text-6xl font-medium leading-none">
              {busy || failed ? "—" : fmt(score)}
            </span>
            <span className="pb-1 text-sm text-inkSoft">/ 100</span>
          </div>
          <p className="mt-2 text-xs text-inkSoft">
            {paper.total_max ? `${fmt(paper.total_awarded)} of ${fmt(paper.total_max)} marks in the scheme` : "Awaiting marks"}
          </p>

          <div className="mt-3 h-1.5 w-40 overflow-hidden rounded-full bg-paperDeep">
            <div
              className="h-full rounded-full bg-red transition-all duration-700"
              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
            />
          </div>

          {accuracy !== null && !busy ? (
            <div className="mt-4 border-t border-dashed border-line pt-3">
              <p className="eyebrow !text-[0.55rem]">Marking accuracy</p>
              <p className="mt-1 flex items-baseline gap-1">
                <span className="display text-2xl font-medium">{accuracy}%</span>
                <span className="text-[0.7rem] text-inkSoft">
                  {accuracy >= 85 ? "key-based" : accuracy >= 70 ? "mostly key-based" : "partly estimated"}
                </span>
              </p>
              {paper.accuracy_note ? (
                <p className="mt-1.5 max-w-[15rem] text-[0.7rem] leading-relaxed text-inkSoft">
                  {paper.accuracy_note}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>

        <div>
          <p className="eyebrow !text-[0.6rem]">Overall feedback</p>
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed">
            {paper.overall_feedback || "Feedback will appear here once this paper is marked."}
          </p>
        </div>
      </section>

      {paper.overall_tips?.length ? (
        <section className="mt-5 rounded-2xl border border-line bg-white p-6">
          <p className="eyebrow !text-[0.6rem]">Improvement plan</p>
          <ol className="mt-4 space-y-3">
            {paper.overall_tips.map((tip, index) => (
              <li key={index} className="flex gap-3 text-sm leading-relaxed">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-paperDeep text-[0.7rem] font-medium">
                  {index + 1}
                </span>
                {tip}
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {paper.knowledge_gaps?.length ? (
        <section className="mt-5 rounded-2xl border border-line bg-white p-6">
          <p className="eyebrow !text-[0.6rem]">Knowledge gaps</p>
          <p className="mt-1 text-xs text-inkSoft">
            The skills behind the lost marks, and where they showed.
          </p>
          <ul className="mt-4 space-y-2.5">
            {paper.knowledge_gaps.map((gap, index) => (
              <li key={index} className="flex gap-3 text-sm leading-relaxed">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red" />
                {gap}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {paper.review_notes?.length ? (
        <section className="mt-5 rounded-2xl border border-[#8a6a10]/30 bg-[#fbf4dc] p-5">
          <p className="eyebrow !text-[0.6rem] !text-[#8a6a10]">Flags for the teacher</p>
          <ul className="mt-3 space-y-1.5">
            {paper.review_notes.map((note, index) => (
              <li key={index} className="text-[0.85rem] leading-relaxed text-[#6b5416]">
                · {note}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="mt-8">
        <div className="flex items-end justify-between gap-3">
          <h2 className="display text-2xl font-medium">Question breakdown</h2>
          <span className="text-xs text-inkSoft">
            {paper.questions?.length || 0} questions marked
          </span>
        </div>

        {paper.questions?.length ? (
          <ul className="mt-3 border-y border-line">
            {paper.questions.map((mark) => (
              <QuestionRow key={mark.id} mark={mark} />
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm italic text-inkSoft">
            Question-level marks appear here once marking finishes.
          </p>
        )}
      </section>
    </>
  );
}
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock3,
  Plus,
  Sparkles,
} from "lucide-react";
import { api } from "./../api/api.js";
import { useAuth } from "./../hooks/useAuth.jsx";

const STATUS_LABEL = {
  draft: "Draft",
  extracting: "Reading",
  extracted: "Read",
  marking: "Marking",
  marked: "Marked",
  review: "Needs review",
  failed: "Failed",
};

function Stamp({ status }) {
  const ok = status === "marked";
  const warn = status === "review";
  return (
    <span
      className={`stamp ${ok ? "text-sage" : warn ? "text-[#8a6a10]" : "text-inkSoft"}`}
    >
      {ok ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : warn ? (
        <AlertCircle className="h-3 w-3" />
      ) : (
        <Clock3 className="h-3 w-3" />
      )}
      {STATUS_LABEL[status] || status}
    </span>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [papers, setPapers] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    Promise.all([api.papers(), api.knowledge()])
      .then(([paperList, sourceList]) => {
        if (!alive) return;
        setPapers(paperList || []);
        setSources(sourceList || []);
      })
      .catch(() => {})
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  const scored = papers.filter((paper) => typeof paper.normalized_score === "number");
  const average = scored.length
    ? Math.round(scored.reduce((sum, paper) => sum + paper.normalized_score, 0) / scored.length)
    : null;
  const reviewCount = papers.filter((paper) => paper.status === "review").length;
  const chunks = sources.reduce((sum, source) => sum + (source.chunk_count || 0), 0);
  const firstName = (user?.full_name || "").split(" ")[0];

  const stats = [
    { label: "Papers marked", value: loading ? "—" : papers.length, note: "in this studio" },
    {
      label: "Average score",
      value: loading ? "—" : average === null ? "—" : average,
      note: "out of 100",
    },
    { label: "Awaiting review", value: loading ? "—" : reviewCount, note: "marks unresolved" },
    {
      label: "Knowledge base",
      value: loading ? "—" : chunks,
      note: `${sources.length} sources`,
    },
  ];

  return (
    <div>
      <section className="fade-up grid gap-10 py-9 lg:grid-cols-[1.1fr_0.9fr] lg:items-end lg:gap-16 lg:py-14">
        <div>
          <p className="eyebrow">
            {firstName ? `Good to see you, ${firstName}` : "Mark scripts · explain every mark"}
          </p>
          <h1 className="display mt-4 text-[2.5rem] font-medium leading-[1.05] text-ink sm:text-[3.3rem]">
            Every script read closely.
            <span className="block italic text-red">Every mark explained.</span>
          </h1>
          <p className="mt-5 max-w-lg text-[0.97rem] leading-relaxed text-inkSoft">
            Upload an unmarked O/L English answer script with its marking scheme. Red Pen reads the
            handwriting, marks each question against the scheme and your syllabus knowledge base, and
            writes the feedback and improvement tips — a score out of 100.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link to="/new" className="ink-btn">
              <Plus className="h-4 w-4" />
              Start a new marking
            </Link>
            <Link to="/knowledge" className="ghost-btn">
              <BookOpen className="h-4 w-4" />
              Knowledge base
            </Link>
          </div>
        </div>

        <div className="paper-card p-6">
          <p className="eyebrow !text-[0.6rem]">How a paper is marked</p>
          <ol className="mt-4 space-y-4">
            {[
              "Upload the scanned script and the marking scheme",
              "Handwriting and printed text are read page by page",
              "Syllabus and past-paper context is retrieved",
              "Each question is marked, then feedback and tips are written",
            ].map((step, index) => (
              <li key={step} className="flex gap-3">
                <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full border border-line text-[0.7rem] font-medium text-ink">
                  {index + 1}
                </span>
                <span className="text-[0.88rem] leading-relaxed text-ink">{step}</span>
              </li>
            ))}
          </ol>
          <p className="mt-5 border-t border-dashed border-line pt-4 text-[0.75rem] italic text-inkSoft">
            Every upload is stored privately — only you can open it.
          </p>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3 border-y border-line py-6 sm:grid-cols-4 sm:gap-6">
        {stats.map((stat) => (
          <div key={stat.label} className="px-1">
            <p className="eyebrow !text-[0.6rem]">{stat.label}</p>
            <p className="display mt-1.5 text-3xl font-medium text-ink">{stat.value}</p>
            <p className="text-[0.72rem] italic text-inkSoft">{stat.note}</p>
          </div>
        ))}
      </section>

      <div className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <section>
          <div className="mb-4 flex items-end justify-between gap-3">
            <h2 className="display text-2xl font-medium text-ink">Recently marked</h2>
            <Link to="/papers" className="flex items-center gap-1 text-[0.8rem] text-red">
              All papers <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((key) => (
                <div key={key} className="h-16 animate-pulse rounded-lg bg-paperDeep" />
              ))}
            </div>
          ) : papers.length === 0 ? (
            <div className="paper-card flex flex-col items-center gap-3 px-6 py-12 text-center">
              <Sparkles className="h-5 w-5 text-red" />
              <p className="display text-lg font-medium text-ink">No papers yet</p>
              <p className="max-w-xs text-[0.85rem] leading-relaxed text-inkSoft">
                Upload your first answer script and scheme. It takes a few minutes to read and mark a
                full paper.
              </p>
              <Link to="/new" className="ink-btn mt-1">
                Mark a paper
              </Link>
            </div>
          ) : (
            <ul className="divide-y divide-line border-y border-line">
              {papers.slice(0, 6).map((paper) => (
                <li key={paper.id}>
                  <Link
                    to={`/papers/${paper.id}`}
                    className="flex items-center justify-between gap-4 py-4 transition hover:bg-paperDeep/50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[0.95rem] font-medium text-ink">
                        {paper.student_name || "Untitled script"}
                      </p>
                      <p className="truncate text-[0.78rem] text-inkSoft">
                        {paper.paper_title || "O/L English"} · {paper.paper_type || "Full paper"}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <Stamp status={paper.status} />
                      <span className="display w-12 text-right text-2xl font-medium text-ink">
                        {typeof paper.normalized_score === "number"
                          ? Math.round(paper.normalized_score)
                          : "—"}
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="paper-card p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-red" />
            <h2 className="display text-xl font-medium text-ink">Knowledge base</h2>
          </div>
          <p className="mt-2 text-[0.83rem] leading-relaxed text-inkSoft">
            Syllabus, past papers and schemes are chunked and indexed. Marking is grounded in what
            they actually ask for.
          </p>

          {loading ? (
            <div className="mt-4 space-y-2">
              {[0, 1, 2].map((key) => (
                <div key={key} className="h-12 animate-pulse rounded bg-paperDeep" />
              ))}
            </div>
          ) : sources.length === 0 ? (
            <p className="mt-4 text-[0.83rem] italic text-inkSoft">
              Nothing indexed yet. Add the syllabus or a past paper to sharpen marking.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {sources.slice(0, 4).map((source) => (
                <li
                  key={source.id}
                  className="flex items-center justify-between gap-3 border-b border-dashed border-line pb-3 last:border-0 last:pb-0"
                >
                  <div className="min-w-0">
                    <p className="truncate text-[0.87rem] font-medium text-ink">{source.title}</p>
                    <p className="text-[0.72rem] italic text-inkSoft">
                      {source.kind}
                      {source.year ? ` · ${source.year}` : ""} · {source.chunk_count || 0} chunks
                    </p>
                  </div>
                  <Sparkles className="h-3.5 w-3.5 shrink-0 text-sage" />
                </li>
              ))}
            </ul>
          )}

          <Link to="/knowledge" className="ghost-btn mt-5 w-full">
            Open knowledge base
          </Link>
        </section>
      </div>
    </div>
  );
}
export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <aside className="hidden flex-col justify-between bg-ink p-12 text-paper lg:flex">
        <div>
          <p className="font-body text-[0.7rem] uppercase tracking-[0.22em] text-paper/60">
            GradeWise AI
          </p>
          <h2 className="display mt-6 max-w-sm text-4xl leading-tight">
            Mark a whole O/L English paper, question by question.
          </h2>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-paper/70">
            Upload the student's script and the marking scheme. Every test is marked against the
            scheme's answer key, with feedback, improvement tips and the skill behind each lost mark.
          </p>
        </div>

        <ul className="space-y-3 text-sm text-paper/70">
          <li>· Runs entirely on your own machine with Ollama — no API key, no cloud</li>
          <li>· Syllabus, past papers and marked papers stay in a local vector store</li>
          <li>· Every paper is reported out of 100</li>
        </ul>
      </aside>

      <div className="flex items-center justify-center px-6 py-14">
        <div className="w-full max-w-sm">
          <p className="eyebrow">Marking studio</p>
          <h1 className="display mt-2 text-3xl font-medium">{title}</h1>
          <p className="mt-1.5 text-sm text-inkSoft">{subtitle}</p>
          <div className="mt-7">{children}</div>
          {footer ? <div className="mt-6 text-sm text-inkSoft">{footer}</div> : null}
        </div>
      </div>
    </div>
  );
}
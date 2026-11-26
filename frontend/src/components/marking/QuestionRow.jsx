import { useState } from "react";
import { AlertCircle, ChevronDown } from "lucide-react";
import { fmt } from "./../../utils/format.js";

const STATUS = {
  full: { label: "Full marks", className: "text-sage" },
  partial: { label: "Partly correct", className: "text-[#8a6a10]" },
  zero: { label: "No marks", className: "text-red" },
  review: { label: "Needs review", className: "text-[#2f5a8f]" },
};

export default function QuestionRow({ mark }) {
  const [open, setOpen] = useState(false);
  const status = STATUS[mark.status] || STATUS.partial;

  return (
    <li className="border-b border-line last:border-0">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center gap-4 py-4 text-left transition hover:bg-paperDeep/40"
      >
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-line bg-white text-[0.78rem] font-medium">
          {mark.question_no}
        </span>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{mark.title || `Question ${mark.question_no}`}</p>
          <p className={`text-[0.72rem] ${status.className}`}>
            {status.label}
            {mark.accuracy ? (
              <span className="text-inkSoft"> · {Math.round(mark.accuracy)}% accuracy</span>
            ) : null}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <span className="display text-lg font-medium">
            {fmt(mark.awarded_marks)}
            <span className="text-[0.8rem] text-inkSoft">/{fmt(mark.max_marks)}</span>
          </span>
          <ChevronDown
            className={`h-4 w-4 text-inkSoft transition-transform ${open ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {open ? (
        <div className="pb-6 sm:pl-14">
          <p className="text-sm leading-relaxed">{mark.feedback}</p>

          {mark.knowledge_gap ? (
            <div className="mt-4 rounded-lg border border-red/30 bg-redWash px-3 py-2.5">
              <p className="eyebrow !text-[0.55rem] !text-red">Knowledge gap</p>
              <p className="mt-1 text-[0.83rem] leading-relaxed">{mark.knowledge_gap}</p>
            </div>
          ) : null}

          {mark.improvement_tips?.length ? (
            <div className="mt-4">
              <p className="eyebrow !text-[0.58rem]">How to improve</p>
              <ul className="mt-2 space-y-1.5">
                {mark.improvement_tips.map((tip, index) => (
                  <li key={index} className="flex gap-2 text-[0.85rem] leading-relaxed">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-red" />
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {mark.scheme_expectation ? (
              <div className="rounded-lg border border-line bg-white p-3">
                <p className="eyebrow !text-[0.55rem]">What the scheme wanted</p>
                <p className="mt-1.5 whitespace-pre-line text-[0.8rem] leading-relaxed text-inkSoft">
                  {mark.scheme_expectation}
                </p>
              </div>
            ) : null}
            {mark.student_answer ? (
              <div className="rounded-lg border border-line bg-white p-3">
                <p className="eyebrow !text-[0.55rem]">What the student wrote</p>
                <p className="mt-1.5 whitespace-pre-line text-[0.8rem] leading-relaxed text-inkSoft">
                  {mark.student_answer}
                </p>
              </div>
            ) : null}
          </div>

          {mark.status === "review" ? (
            <p className="mt-3 flex items-center gap-1.5 text-[0.75rem] text-[#2f5a8f]">
              <AlertCircle className="h-3.5 w-3.5" /> Check this mark against the original script.
            </p>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
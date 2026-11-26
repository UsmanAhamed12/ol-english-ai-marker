"""The marking pipeline, expressed as a LangGraph state machine.

validate_documents -> render_pages -> run_ocr -> validate_ocr
    -> read_inventory -> retrieve_context -> mark_questions -> persist_results
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal
from app.models import MarkingJob, QuestionMark
from app.rag import loaders as documents, retriever as rag
from app.rag.llm import AIError
from app.rag.chains import inventory_chain, marking_chain


class PipelineError(RuntimeError):
    """An error whose message is safe to show to the teacher."""


class MarkingState(TypedDict, total=False):
    job_id: str
    user_id: str
    paper_title: str
    paper_type: str
    script_files: list[dict]
    scheme_files: list[dict]
    script_pages: list[dict]
    scheme_pages: list[dict]
    script_text: str
    scheme_text: str
    flags: list[str]
    readable: bool
    inventory: list[dict]
    context: str
    result: dict


# ----------------------------------------------------------------- helpers


def _round(value, places: int = 1) -> float:
    return round(float(value or 0), places)


def _clean_no(value) -> str:
    return re.sub(r"^(question|test|q)\s*", "", str(value or "").strip(), flags=re.I)[:20]


def _key(value) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _preview(text: str) -> str:
    return text if len(text) <= 12000 else text[:12000] + "\n\n[… shortened for storage …]"


def _set_job(db: Session, job_id: str, **fields) -> None:
    job = db.get(MarkingJob, job_id)
    if job is None:
        return
    for key, value in fields.items():
        setattr(job, key, value)
    db.commit()


def _normalise_to_hundred(rows: list[dict]) -> list[dict]:
    """Every paper is out of 100: scale the allocations when they don't add up."""
    if not rows:
        return rows
    total = sum(float(row.get("max_marks") or 0) for row in rows)
    if not total or abs(total - 100) < 0.01:
        return rows

    factor = 100 / total
    half = lambda n: round(float(n or 0) * 2) / 2  # noqa: E731
    scaled = []
    for row in rows:
        maximum = max(0.5, half((row.get("max_marks") or 0) * factor))
        scaled.append(
            {
                **row,
                "max_marks": maximum,
                "awarded_marks": min(maximum, half((row.get("awarded_marks") or 0) * factor)),
            }
        )

    drift = _round(100 - sum(row["max_marks"] for row in scaled))
    if drift:
        biggest = max(range(len(scaled)), key=lambda i: scaled[i]["max_marks"])
        row = scaled[biggest]
        maximum = _round(row["max_marks"] + drift)
        scaled[biggest] = {
            **row,
            "max_marks": maximum,
            "awarded_marks": min(row["awarded_marks"], maximum),
        }
    return scaled


def _keyed_tests(scheme_text: str) -> set[str]:
    return {m.replace("Test", "").strip() for m in re.findall(r"tests?\s*[-–]?\s*(\d+)", scheme_text or "", re.I)}


def _accuracy(row: dict, has_key: bool) -> int:
    value = 55 if not has_key else 72 if row["status"] == "review" else 96
    answer = row.get("student_answer") or ""
    if not answer:
        value -= 8
    elif "illegible" in answer.lower():
        value -= 18
    return max(20, min(98, value))


# ----------------------------------------------------------------- nodes


def validate_documents(state: MarkingState) -> dict:
    script = state.get("script_files") or []
    if not script:
        raise PipelineError("No answer script file on this paper.")
    for record in script + (state.get("scheme_files") or []):
        if not Path(record["path"]).is_file():
            raise PipelineError("One of the uploaded files is no longer available. Upload it again.")
    with SessionLocal() as db:
        _set_job(db, state["job_id"], status="extracting", error_message="")
    return {}


def render_pages(state: MarkingState) -> dict:
    return {
        "script_pages": documents.read_pages(state.get("script_files") or [], separate_ink=True),
        "scheme_pages": documents.read_pages(state.get("scheme_files") or []),
    }


def run_ocr(state: MarkingState) -> dict:
    script_text, script_flags = documents.run_ocr(state.get("script_pages") or [], "script")
    scheme_text, scheme_flags = documents.run_ocr(state.get("scheme_pages") or [], "scheme")

    with SessionLocal() as db:
        _set_job(
            db,
            state["job_id"],
            status="extracted",
            extracted_script=_preview(script_text),
            extracted_scheme=_preview(scheme_text),
        )

    return {
        "script_text": script_text,
        "scheme_text": scheme_text,
        "flags": script_flags + scheme_flags,
    }


def validate_ocr(state: MarkingState) -> dict:
    script_text = state.get("script_text") or ""
    readable = len(script_text.strip()) >= 40
    return {"readable": readable}


def cannot_read(state: MarkingState) -> dict:
    flags = state.get("flags") or []
    if flags:
        reason = f"The answer script could not be read. {flags[0]}"
    else:
        reason = (
            "The answer script could not be read. No text came through — check that the scan is "
            "upright and legible, then try again."
        )

    with SessionLocal() as db:
        _set_job(db, state["job_id"], status="failed", error_message=reason[:480])
    return {}


def read_inventory(state: MarkingState) -> dict:
    with SessionLocal() as db:
        _set_job(db, state["job_id"], status="marking")

    scheme_text = (state.get("scheme_text") or "")[: settings.prompt_chars]
    script_text = (state.get("script_text") or "")[: settings.prompt_chars]
    if len(scheme_text) + len(script_text) < 120:
        return {"inventory": []}

    try:
        data = inventory_chain(scheme_text, script_text)
    except AIError:
        # Without an inventory the paper is still marked, just without the checklist.
        return {"inventory": []}

    items = data.get("questions") if isinstance(data, dict) else None
    inventory = []
    for index, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        inventory.append(
            {
                "question_no": _clean_no(item.get("question_no")) or str(index + 1),
                "title": str(item.get("title") or "")[:200],
                "max_marks": _round(item.get("max_marks")),
            }
        )
    return {"inventory": inventory[:40]}


def retrieve_context(state: MarkingState) -> dict:
    # Syllabus / past-paper / worked-example chunks from the local knowledge base.
    context = rag.search(
        state["user_id"],
        f"{state.get('scheme_text') or ''}\n{state.get('script_text') or ''}",
    )
    return {"context": context}


def mark_questions(state: MarkingState) -> dict:
    class JobView:
        paper_title = state.get("paper_title") or ""
        paper_type = state.get("paper_type") or "Full paper"

    return {
        "result": marking_chain(
            JobView(),
            (state.get("script_text") or "")[: settings.prompt_chars],
            (state.get("scheme_text") or "")[: settings.prompt_chars],
            state.get("context") or "",
            state.get("inventory") or [],
        )
    }


def persist_results(state: MarkingState) -> dict:
    result = state.get("result") or {}
    raw_questions = result.get("questions") if isinstance(result, dict) else None
    flags = list(state.get("flags") or [])

    rows: list[dict] = []
    for index, item in enumerate(raw_questions or []):
        if not isinstance(item, dict):
            continue
        maximum = float(item.get("max_marks") or 0)
        awarded = max(0.0, min(float(item.get("awarded_marks") or 0), maximum))
        status = item.get("status") if item.get("status") in {"full", "partial", "zero", "review"} else "partial"
        rows.append(
            {
                "question_no": _clean_no(item.get("question_no")) or str(index + 1),
                "title": str(item.get("title") or "")[:300],
                "max_marks": _round(maximum),
                "awarded_marks": _round(awarded),
                "status": status,
                "scheme_expectation": str(item.get("scheme_expectation") or "")[:4000],
                "student_answer": str(item.get("student_answer") or "")[:4000],
                "feedback": str(item.get("feedback") or "")[:4000],
                "improvement_tips": [str(tip)[:400] for tip in (item.get("improvement_tips") or [])][:4],
                "knowledge_gap": str(item.get("knowledge_gap") or "")[:400],
                "sort_order": index,
            }
        )

    review_notes = [str(note)[:400] for note in (result.get("review_notes") or [])][:12]

    # One line per question in the scheme, in scheme order, even when the model
    # skips a question or the scan lost a page.
    inventory = state.get("inventory") or []
    used: set[int] = set()
    final: list[dict] = []
    for item in inventory:
        match = next(
            (
                index
                for index, row in enumerate(rows)
                if index not in used and _key(row["question_no"]) == _key(item["question_no"])
            ),
            None,
        )
        if match is not None:
            used.add(match)
            final.append({**rows[match], "sort_order": len(final)})
            continue
        final.append(
            {
                "question_no": item["question_no"],
                "title": item["title"],
                "max_marks": _round(item["max_marks"]),
                "awarded_marks": 0,
                "status": "zero",
                "scheme_expectation": "",
                "student_answer": "",
                "feedback": "No attempt for this question was found in the scanned script.",
                "improvement_tips": [
                    "Attempt every question - an unanswered question scores zero however strong the rest of the paper is."
                ],
                "knowledge_gap": "This whole question was left unanswered.",
                "sort_order": len(final),
            }
        )
        review_notes.append(f"Question {item['question_no']} had no answer in the scan - check the original script.")

    for index, row in enumerate(rows):
        if index not in used:
            final.append({**row, "sort_order": len(final)})

    final = _normalise_to_hundred(final)

    keyed = _keyed_tests(state.get("scheme_text") or "")
    keyed_count = 0
    for row in final:
        has_key = "".join(ch for ch in str(row["question_no"]) if ch.isdigit()) in keyed
        row["accuracy"] = _accuracy(row, has_key)
        keyed_count += 1 if has_key else 0

    weight = sum(row["max_marks"] or 1 for row in final) or 1
    accuracy = round(sum(row["accuracy"] * (row["max_marks"] or 1) for row in final) / weight)
    accuracy_note = (
        f"{keyed_count} of {len(final)} tests were marked item by item against the scheme's answer key; "
        f"{len(final) - keyed_count} were estimated from the paper itself because the scheme has no key for them."
    )

    total_max = _round(sum(row["max_marks"] for row in final))
    total_awarded = _round(sum(row["awarded_marks"] for row in final))
    normalized = _round((total_awarded / total_max) * 100, 1) if total_max else 0

    needs_review = any(row["status"] == "review" for row in final) or bool(review_notes)
    if flags:
        review_notes.extend(flags[:4])

    with SessionLocal() as db:
        db.query(QuestionMark).filter(QuestionMark.job_id == state["job_id"]).delete()
        db.add_all(
            [
                QuestionMark(job_id=state["job_id"], user_id=state["user_id"], **row)
                for row in final
            ]
        )
        job = db.get(MarkingJob, state["job_id"])
        if job is not None:
            job.total_max = total_max
            job.total_awarded = total_awarded
            job.normalized_score = normalized
            job.accuracy = accuracy
            job.accuracy_note = accuracy_note
            job.overall_feedback = str(result.get("overall_feedback") or "")[:6000]
            job.overall_tips = [str(tip)[:400] for tip in (result.get("overall_tips") or [])][:6]
            job.knowledge_gaps = [str(gap)[:400] for gap in (result.get("knowledge_gaps") or [])][:6]
            job.review_notes = review_notes
            job.status = "review" if needs_review else "marked"
            job.marked_at = datetime.now(timezone.utc)
            job.error_message = ""
        db.commit()

        # Feed the finished paper back into the knowledge base as a worked example.
        title = state.get("paper_title") or (job.student_name if job is not None else "")
        try:
            rag.index_example(state["user_id"], state["job_id"], title, final, normalized)
        except Exception:  # noqa: BLE001 - indexing must never undo a marked paper
            pass

    return {}


def _route_after_ocr(state: MarkingState) -> str:
    return "read_inventory" if state.get("readable") else "cannot_read"


def build_graph():
    graph = StateGraph(MarkingState)
    graph.add_node("validate_documents", validate_documents)
    graph.add_node("render_pages", render_pages)
    graph.add_node("run_ocr", run_ocr)
    graph.add_node("validate_ocr", validate_ocr)
    graph.add_node("cannot_read", cannot_read)
    graph.add_node("read_inventory", read_inventory)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("mark_questions", mark_questions)
    graph.add_node("persist_results", persist_results)

    graph.add_edge(START, "validate_documents")
    graph.add_edge("validate_documents", "render_pages")
    graph.add_edge("render_pages", "run_ocr")
    graph.add_edge("run_ocr", "validate_ocr")
    graph.add_conditional_edges(
        "validate_ocr", _route_after_ocr, {"read_inventory": "read_inventory", "cannot_read": "cannot_read"}
    )
    graph.add_edge("read_inventory", "retrieve_context")
    graph.add_edge("retrieve_context", "mark_questions")
    graph.add_edge("mark_questions", "persist_results")
    graph.add_edge("persist_results", END)
    graph.add_edge("cannot_read", END)
    return graph.compile()


GRAPH = build_graph()


def run_marking(job_id: str) -> None:
    """Background entry point: runs the graph and always leaves a final status."""
    with SessionLocal() as db:
        job = db.get(MarkingJob, job_id)
        if job is None:
            return
        state: MarkingState = {
            "job_id": job.id,
            "user_id": job.user_id,
            "paper_title": job.paper_title,
            "paper_type": job.paper_type,
            "script_files": list(job.script_files or []),
            "scheme_files": list(job.scheme_files or []),
            "flags": [],
        }

    try:
        GRAPH.invoke(state)
    except PipelineError as exc:
        _fail(job_id, str(exc))
    except AIError as exc:
        _fail(job_id, str(exc))
    except Exception as exc:  # noqa: BLE001 - local studio: name the real cause
        _fail(job_id, f"Marking stopped part-way through ({type(exc).__name__}: {str(exc)[:160]}).")


def _fail(job_id: str, message: str) -> None:
    with SessionLocal() as db:
        _set_job(db, job_id, status="failed", error_message=message[:480])
"""The knowledge base: chunked in SQLite, retrieved two ways.

SQLite holds the text and is the single source of truth. Retrieval has two paths:

  * **dense** (`vectorstore.py`) — LlamaIndex embeds the chunks with an Ollama
    embedding model and searches a per-teacher Chroma collection. This is the
    default and is what a marking run normally uses.
  * **lexical** — the scorer below, which needs nothing but the database. It is
    used automatically when the vector store or embedding model is unavailable,
    and it can be forced with RETRIEVAL_MODE=lexical.

Everything is scoped per teacher. Two kinds of content live here:
  * knowledge sources — syllabus, past papers, marking schemes, guidance
  * worked examples — finished papers, stored under the hidden kind
    "Worked example" so later papers are marked in the same house style
"""

import re

from app.rag.splitter import chunk_text, terms

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal
from app.models import Chunk, KnowledgeSource
from app.rag import vectorstore

EXAMPLE_KIND = "Worked example"



# ---------------------------------------------------------------- indexing


def index_source(db: Session, source: KnowledgeSource) -> int:
    """(Re)build the chunks of one source. Returns the number stored."""
    db.query(Chunk).filter(Chunk.source_id == source.id).delete()

    pieces = chunk_text(source.content or "")
    for ordinal, text in enumerate(pieces):
        db.add(
            Chunk(
                source_id=source.id,
                user_id=source.user_id,
                ordinal=ordinal,
                text=text,
                terms=" ".join(sorted(set(terms(text)))),
                length=len(text),
            )
        )

    source.chunk_count = len(pieces)
    db.commit()
    vectorstore.mark_dirty(source.user_id)
    return len(pieces)


def reindex_missing(user_id: str) -> None:
    """Older installs stored vectors elsewhere; rebuild any source without chunks."""
    with SessionLocal() as db:
        sources = (
            db.query(KnowledgeSource)
            .filter(KnowledgeSource.user_id == user_id)
            .all()
        )
        for source in sources:
            count = db.query(func.count(Chunk.id)).filter(Chunk.source_id == source.id).scalar()
            if not count:
                index_source(db, source)


def index_example(
    user_id: str, job_id: str, title: str, rows: list[dict], score: float
) -> int:
    """Store a marked paper as a worked example for future retrieval."""
    if not rows:
        return 0

    marker = f"job:{job_id}"
    lines = [f"Marked example: {title or 'O/L English paper'}. Final score {score}/100."]
    for row in rows:
        lines.append(
            "Test {no} - {title} ({awarded}/{maximum}). Scheme wanted: {scheme}. "
            "Examiner feedback: {feedback} Gap: {gap}.".format(
                no=row.get("question_no", ""),
                title=row.get("title") or "question",
                awarded=row.get("awarded_marks", 0),
                maximum=row.get("max_marks", 0),
                scheme=(row.get("scheme_expectation") or "see scheme")[:600],
                feedback=(row.get("feedback") or "")[:600],
                gap=(row.get("knowledge_gap") or "")[:300],
            )
        )

    with SessionLocal() as db:
        source = (
            db.query(KnowledgeSource)
            .filter(KnowledgeSource.user_id == user_id, KnowledgeSource.notes == marker)
            .first()
        )
        if source is None:
            source = KnowledgeSource(user_id=user_id, notes=marker)
            db.add(source)
        source.title = f"Worked example · {(title or 'O/L English')[:160]}"
        source.kind = EXAMPLE_KIND
        source.year = ""
        source.content = "\n\n".join(lines)[:120000]
        db.commit()
        db.refresh(source)
        return index_source(db, source)


def delete_source(source_id: str) -> None:
    with SessionLocal() as db:
        db.query(Chunk).filter(Chunk.source_id == source_id).delete()
        db.commit()


def delete_example(job_id: str) -> None:
    with SessionLocal() as db:
        sources = (
            db.query(KnowledgeSource)
            .filter(KnowledgeSource.notes == f"job:{job_id}")
            .all()
        )
        for source in sources:
            db.query(Chunk).filter(Chunk.source_id == source.id).delete()
            db.delete(source)
        db.commit()


def counts(user_id: str) -> dict:
    """What the knowledge base holds for this teacher."""
    with SessionLocal() as db:
        def total(condition=None) -> int:
            query = (
                db.query(func.count(Chunk.id))
                .join(KnowledgeSource, Chunk.source_id == KnowledgeSource.id)
                .filter(KnowledgeSource.user_id == user_id)
            )
            if condition is not None:
                query = query.filter(condition)
            return int(query.scalar() or 0)

        return {
            "vectors": total(),
            "knowledge_chunks": total(KnowledgeSource.kind != EXAMPLE_KIND),
            "example_chunks": total(KnowledgeSource.kind == EXAMPLE_KIND),
            "index": vectorstore.status(user_id),
        }


# ---------------------------------------------------------------- retrieval


def search(user_id: str, query: str, limit: int | None = None) -> str:
    """Rubric text for this paper, formatted for the marking prompt.

    Dense retrieval (LlamaIndex over Chroma) is tried first. It returns "" when it
    cannot run, and the lexical scorer below then answers, so marking never stops
    because a model is missing.
    """
    dense = vectorstore.search(user_id, query, limit)
    if dense:
        return dense
    return search_lexical(user_id, query, limit)


def search_lexical(user_id: str, query: str, limit: int | None = None) -> str:
    """Chunks that overlap most with the paper. Needs no model at all."""
    query_terms = set(terms((query or "")[:4000]))
    if not query_terms:
        return ""

    with SessionLocal() as db:
        rows = (
            db.query(Chunk.text, KnowledgeSource.kind, KnowledgeSource.title)
            .join(KnowledgeSource, Chunk.source_id == KnowledgeSource.id)
            .filter(KnowledgeSource.user_id == user_id)
            .all()
        )

    scored: list[tuple[int, str, str, str]] = []
    for text, kind, title in rows:
        score = sum(1 for term in terms(text) if term in query_terms)
        if score > 0:
            scored.append((score, kind or "Knowledge", title or "", text))

    if not scored:
        return ""

    scored.sort(key=lambda row: row[0], reverse=True)
    parts: list[str] = []
    used = 0
    for _score, kind, title, text in scored[: limit or settings.retrieval_k]:
        block = f"[{kind} · {title}]\n{text}".strip()
        if used + len(block) > settings.retrieval_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)
"""Everything that changes the knowledge base.

The route file (``api/v1/routes/rubrics.py``) and the ingestion script both call
these functions, so a document stored from the command line behaves exactly like
one uploaded in the browser: same validation, same chunking, same indexing.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import KnowledgeSource, MarkingJob, QuestionMark, User
from app.rag import retriever
from app.services import starter_knowledge

KINDS = {"Syllabus", "Past paper", "Marking scheme", "Guidance"}
MIN_CHARS = 40
MAX_CHARS = 120_000


def store_source(
    db: Session,
    user: User,
    title: str,
    kind: str,
    year: str = "",
    notes: str = "",
    content: str = "",
) -> KnowledgeSource:
    """Validate the text, save the source, and build its chunks."""
    content = (content or "").strip()[:MAX_CHARS]
    if len(content) < MIN_CHARS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "This document had no readable text. Try a clearer scan, or paste the text instead.",
        )

    source = KnowledgeSource(
        user_id=user.id,
        title=(title or "").strip()[:200] or "Untitled document",
        kind=kind if kind in KINDS else "Syllabus",
        year=(year or "")[:40],
        notes=(notes or "")[:500],
        content=content,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    retriever.index_source(db, source)
    db.refresh(source)
    return source


def list_sources(db: Session, user: User) -> list[KnowledgeSource]:
    """The teacher's own documents, oldest first. Worked examples stay hidden."""
    starter_knowledge.ensure(db, user.id)
    retriever.reindex_missing(user.id)

    return (
        db.query(KnowledgeSource)
        .filter(
            KnowledgeSource.user_id == user.id,
            KnowledgeSource.kind != retriever.EXAMPLE_KIND,
        )
        .order_by(KnowledgeSource.created_at.asc())
        .limit(100)
        .all()
    )


def delete_source(db: Session, user: User, source_id: str) -> None:
    source = (
        db.query(KnowledgeSource)
        .filter(KnowledgeSource.id == source_id, KnowledgeSource.user_id == user.id)
        .first()
    )
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")

    retriever.delete_source(source.id)
    db.delete(source)
    db.commit()


def counts(user: User) -> dict:
    """What the knowledge base currently holds for this teacher."""
    return retriever.counts(user.id)


def index_marked_papers(db: Session, user: User) -> dict:
    """Store every marked paper as a worked example for future retrieval."""
    jobs = (
        db.query(MarkingJob)
        .filter(MarkingJob.user_id == user.id, MarkingJob.status.in_(["marked", "review"]))
        .order_by(MarkingJob.created_at.desc())
        .limit(100)
        .all()
    )

    indexed = 0
    for job in jobs:
        rows = [
            {
                "question_no": mark.question_no,
                "title": mark.title,
                "max_marks": mark.max_marks,
                "awarded_marks": mark.awarded_marks,
                "scheme_expectation": mark.scheme_expectation,
                "feedback": mark.feedback,
                "knowledge_gap": mark.knowledge_gap,
            }
            for mark in db.query(QuestionMark)
            .filter(QuestionMark.job_id == job.id)
            .order_by(QuestionMark.sort_order)
            .all()
        ]
        if not rows:
            continue
        retriever.index_example(
            user.id,
            job.id,
            job.paper_title or job.student_name,
            rows,
            job.normalized_score,
        )
        indexed += 1

    return {"papers": indexed, "vectors": retriever.counts(user.id)}
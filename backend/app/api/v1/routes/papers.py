"""Uploading an answer script and browsing the papers already marked.

Two endpoints here create work, and both hand the actual marking to a background
task so the browser gets its 201 immediately and polls the paper while the local
model works through the sixteen tests.
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.limits import limiter
from app.models import MarkingJob, User
from app.schemas import PaperOut, PaperSummary
from app.services.marking_service import run_marking
from app.utils import files as storage

router = APIRouter(prefix="/api/papers", tags=["papers"])


def _label(files: list[dict]) -> str:
    """A readable title from the uploaded filename, so the list is not all 'untitled'."""
    name = (files[0].get("name") if files else "") or "Untitled script"
    stem = name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
    return (stem or "Untitled script")[:80]


def own_paper(db: Session, paper_id: str, user: User) -> MarkingJob:
    """Fetch one paper, but only if it belongs to the signed-in teacher."""
    job = (
        db.query(MarkingJob)
        .filter(MarkingJob.id == paper_id, MarkingJob.user_id == user.id)
        .first()
    )
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paper not found.")
    return job


@router.post("", response_model=PaperSummary, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/hour")
async def create_paper(
    request: Request,
    background_tasks: BackgroundTasks,
    script: list[UploadFile] = File(...),
    scheme: list[UploadFile] = File(default=[]),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarkingJob:
    """Store the script and its scheme, then start marking in the background."""
    if not script:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload the student's answer script.")
    if not scheme:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload the marking scheme for this paper.")

    script_files = await storage.save_uploads(script, "scripts")
    try:
        scheme_files = await storage.save_uploads(scheme, "schemes")
    except HTTPException:
        # The scheme was rejected: do not leave the script orphaned on disk.
        storage.remove_all(script_files)
        raise

    label = _label(script_files)
    job = MarkingJob(
        user_id=user.id,
        student_name=label,
        paper_title=f"{label} · full paper",
        paper_type="Full paper",
        status="extracting",
        script_files=script_files,
        scheme_files=scheme_files,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_marking, job.id)
    return job


@router.get("", response_model=list[PaperSummary])
def list_papers(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MarkingJob]:
    """The fifty most recent papers, newest first."""
    return (
        db.query(MarkingJob)
        .filter(MarkingJob.user_id == user.id)
        .order_by(MarkingJob.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(
    paper_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MarkingJob:
    """One paper with every question mark, used by the detail page while polling."""
    return own_paper(db, paper_id, user)
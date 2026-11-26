"""Bulk-load the knowledge base from ``data/raw`` without opening the browser.

Put your own documents in the folders, then run this once:

    cd backend
    source .venv/bin/activate
    python -m scripts.ingest --email you@example.com

The folder a file sits in decides its kind:

    data/raw/mark_schemes/      -> Marking scheme
    data/raw/rubrics/           -> Syllabus
    data/raw/past_papers/       -> Past paper
    data/raw/examiner_reports/  -> Guidance

Files already stored (same title) are skipped, so the script is safe to re-run.
"""

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.db import SessionLocal, init_db  # noqa: E402
from app.models import KnowledgeSource, User  # noqa: E402
from app.services import ingestion_service, rubric_service  # noqa: E402

FOLDERS = {
    "mark_schemes": "Marking scheme",
    "rubrics": "Syllabus",
    "past_papers": "Past paper",
    "examiner_reports": "Guidance",
}
SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def _records(folder: Path) -> list[dict]:
    """Every readable file in one folder, in the shape the loaders expect."""
    return [
        {"path": str(path), "name": path.name, "relative": path.name}
        for path in sorted(folder.iterdir())
        if path.is_file() and path.suffix.lower() in SUFFIXES
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest data/raw into the local knowledge base.")
    parser.add_argument("--email", required=True, help="The teacher account the documents belong to.")
    parser.add_argument("--dir", default=str(BACKEND / "data" / "raw"), help="Folder to read from.")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"No such folder: {root}")
        return 1

    init_db()
    stored = 0

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == args.email.strip().lower()).first()
        if user is None:
            print(f"No account for {args.email}. Register in the studio first.")
            return 1

        for folder_name, kind in FOLDERS.items():
            folder = root / folder_name
            if not folder.is_dir():
                continue

            for record in _records(folder):
                title = Path(record["name"]).stem.replace("_", " ").replace("-", " ").strip()
                exists = (
                    db.query(KnowledgeSource)
                    .filter(KnowledgeSource.user_id == user.id, KnowledgeSource.title == title)
                    .first()
                )
                if exists is not None:
                    print(f"skip   {title} (already stored)")
                    continue

                print(f"read   {record['name']} ...", end=" ", flush=True)
                try:
                    content, flags = ingestion_service.text_from_records([record])
                except Exception as error:  # noqa: BLE001 - report and carry on
                    print(f"failed ({type(error).__name__})")
                    continue

                try:
                    rubric_service.store_source(db, user, title, kind, "", "Ingested from data/raw", content)
                except Exception as error:  # noqa: BLE001 - one bad file must not stop the run
                    reason = flags[0] if flags else type(error).__name__
                    print(f"failed ({reason})")
                    continue

                stored += 1
                print(f"ok ({len(content)} characters)")

    print(f"\n{stored} document(s) added to the knowledge base.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
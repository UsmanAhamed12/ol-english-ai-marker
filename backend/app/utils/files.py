"""Upload validation and private file storage.

Files never become publicly reachable: they are written under `private_dir`
with a random name and only streamed back through an authenticated endpoint.
"""

import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED = {
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}


def _sniff_ok(head: bytes, suffix: str) -> bool:
    return any(head.startswith(sig) for sig in ALLOWED.get(suffix, ()))


async def save_uploads(files: list[UploadFile], folder: str) -> list[dict]:
    """Validate and store uploads. Returns [{"name", "path", "relative"}]."""
    if not files:
        return []
    if len(files) > settings.max_files:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"At most {settings.max_files} files.")

    target_dir = settings.upload_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    saved: list[dict] = []
    for upload in files:
        original = Path(upload.filename or "page")
        suffix = original.suffix.lower()
        if suffix not in ALLOWED:
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only PDF, JPG or PNG files are accepted.")

        data = await upload.read(settings.max_upload_bytes + 1)
        await upload.close()

        if not data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "One of the files was empty.")
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"Each file must be under {settings.max_upload_mb} MB.",
            )
        if not _sniff_ok(data[:16], suffix):
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "That file is not a real PDF or image.")

        stored = f"{uuid.uuid4().hex}{suffix}"
        path = target_dir / stored
        with open(path, "wb") as handle:
            handle.write(data)

        saved.append(
            {
                "name": original.name[:120],
                "relative": f"{folder}/{stored}",
                "path": str(path),
                "bytes": len(data),
            }
        )
    return saved


def resolve(relative: str) -> Path:
    """Resolve a stored relative path, refusing anything outside the upload root."""
    root = settings.upload_dir
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found.")
    if not candidate.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found.")
    return candidate


def remove_all(records: list[dict]) -> None:
    for record in records or []:
        try:
            path = resolve(record.get("relative", ""))
            os.unlink(path)
        except (HTTPException, OSError):
            continue
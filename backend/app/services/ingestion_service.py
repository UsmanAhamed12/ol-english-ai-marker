"""Turning an uploaded document into text the knowledge base can index.

The order matters and is the same for every caller:

    save the upload -> render pages -> OCR each page -> delete the upload

The temporary file is deleted in a ``finally`` block, so a failed read never
leaves a teacher's document sitting in the uploads folder.
"""

from app.rag import loaders
from app.utils import files as file_store


def text_from_records(records: list[dict]) -> tuple[str, list[str]]:
    """Page images -> OCR text. Raises ``AIError`` when Ollama is unreachable."""
    pages = loaders.read_pages(records)
    return loaders.run_ocr(pages, "ingest")


async def read_upload(uploads) -> tuple[str, list[str]]:
    """Save the uploads, read them, and always clean up afterwards."""
    saved = await file_store.save_uploads(uploads, "knowledge")
    try:
        return text_from_records(saved)
    finally:
        file_store.remove_all(saved)
"""Page text + page images from uploaded PDFs and photographs.

A script page becomes either text (a PDF with a real text layer) or an image.
Script images are split by ink colour into a printed layer and a handwritten
layer (app/rag/ink.py) and each layer is read separately by GLM-OCR, so the
marker always knows which words are the question and which are the student's.
"""

import base64
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageOps

from app.core.config import settings
from app.rag.ink import split_ink
from app.rag.llm import ocr_image

# Longest side of a photographed page sent to the OCR model, in pixels.
MAX_SIDE = 2400


def _pil_from_page(page: fitz.Page) -> Image.Image:
    pixmap = page.get_pixmap(dpi=settings.ocr_dpi, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def _pil_from_file(path: Path) -> Image.Image:
    image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if max(image.size) > MAX_SIDE:
        image.thumbnail((MAX_SIDE, MAX_SIDE))
    return image


def _jpeg_b64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=settings.ocr_quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _page_record(name: str, number: int, text: str, image: Image.Image | None, separate_ink: bool) -> dict:
    record = {"name": name, "page": number, "text": text, "image": None, "mime": "", "layers": None}
    if image is None:
        return record
    record["image"] = _jpeg_b64(image)
    record["mime"] = "image/jpeg"
    if separate_ink:
        record["layers"] = split_ink(image, settings.ink_min_pixels)
    return record


def read_pages(paths: list[dict], *, separate_ink: bool = False) -> list[dict]:
    """Every uploaded file as pages: printed text where the PDF has it, an image where not."""
    pages: list[dict] = []

    for record in paths:
        if len(pages) >= settings.max_pages:
            break

        path = Path(record["path"])
        name = record.get("name") or path.name

        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            pages.append(_page_record(name, 1, "", _pil_from_file(path), separate_ink))
            continue

        with fitz.open(path) as doc:
            for index, page in enumerate(doc, start=1):
                if len(pages) >= settings.max_pages:
                    break
                text = (page.get_text("text") or "").strip()
                scanned = len(text) < settings.ocr_min_chars
                image = _pil_from_page(page) if scanned else None
                pages.append(_page_record(name, index, text, image, separate_ink))
    return pages


def _shorten(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rstrip() + " ..."


def _read(image_b64: str, mime: str, label: str, page: dict, flags: list[str]) -> str:
    """One OCR call. A failure becomes a flag, never a lost paper."""
    try:
        text = ocr_image(image_b64, mime)
    except Exception as exc:  # noqa: BLE001 - one bad page must not lose the rest
        flags.append(f"Page {page['page']} of {page['name']} ({label}): {str(exc)[:160]}")
        return ""
    if not text:
        flags.append(f"Page {page['page']} of {page['name']} ({label}) came back blank.")
    return text


def read_script_page(page: dict, flags: list[str]) -> str:
    """Printed and handwritten text of one script page, kept apart."""
    layers = page["layers"]
    header = f"--- Page {page['page']} ---"

    if layers is not None and layers.handwritten_b64:
        printed = _read(layers.printed_b64, "image/png", "printed layer", page, flags)
        written = _read(layers.handwritten_b64, "image/png", "handwritten layer", page, flags)
        printed = _shorten(printed, settings.printed_chars_per_page)
        return f"{header}\n[PRINTED]\n{printed}\n[HANDWRITTEN]\n{written or '(nothing read)'}"

    # No coloured pen on this page: blank, a black-pen answer or a photocopy.
    mixed = _read(page["image"], page["mime"] or "image/jpeg", "whole page", page, flags)
    if mixed:
        flags.append(
            f"Page {page['page']} of {page['name']}: no coloured pen found, so printed and "
            "handwritten text could not be told apart. Check this page by eye."
        )
    return f"{header}\n[PRINTED + HANDWRITTEN, NOT SEPARATED]\n{mixed}" if mixed else ""


def run_ocr(pages: list[dict], kind: str) -> tuple[str, list[str]]:
    """Read the scanned pages, keep printed text as-is. Returns (text, flags).

    kind "script" separates printed from handwritten ink; "scheme" and "ingest"
    are printed documents and are read whole.
    """
    chunks: list[str] = []
    flags: list[str] = []

    for page in pages:
        if page.get("image") is None:
            if page["text"]:
                chunks.append(page["text"])
            continue

        if kind == "script":
            chunk = read_script_page(page, flags)
        else:
            chunk = _read(page["image"], page["mime"] or "image/jpeg", "page", page, flags)
        if chunk:
            chunks.append(chunk)

    return "\n\n".join(chunk for chunk in chunks if chunk).strip(), flags

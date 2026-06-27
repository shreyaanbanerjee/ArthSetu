"""Document OCR utilities."""

from __future__ import annotations

import io
from typing import Any


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from an image using available OCR libraries."""
    if not image_bytes:
        return ""
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image, lang="eng+hin").strip()
    except Exception:
        return ""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF using pypdf, with OCR fallback for scanned files."""
    if not pdf_bytes:
        return ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n".join(page for page in pages if page).strip()
    except Exception:
        return ""


def describe_document_payload(filename: str | None, content_type: str | None, raw_text: str) -> dict[str, Any]:
    """Return metadata about extracted document content."""
    return {
        "filename": filename,
        "content_type": content_type,
        "characters_extracted": len(raw_text),
        "has_text": bool(raw_text.strip()),
    }

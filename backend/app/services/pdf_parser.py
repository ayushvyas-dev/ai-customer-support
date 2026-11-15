import io
import logging
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "document.pdf") -> tuple[str, list[dict[str, Any]]]:
    """Parse raw bytes of a PDF file into full text and structured per-page text objects.

    Args:
        pdf_bytes: Raw binary content of the PDF.
        filename: Optional filename for logging and error reporting.

    Returns:
        tuple containing:
            - full_text: Combined string of all pages.
            - pages: List of dicts, each with {"page": int, "text": str}.

    Raises:
        ValueError: If PDF is empty, corrupt, or contains no readable text stream.
    """
    if not pdf_bytes or len(pdf_bytes) < 4:
        raise ValueError(f"Empty or incomplete PDF bytes for file '{filename}'")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as ex:
        raise ValueError(f"Corrupt or invalid PDF file '{filename}': {ex}") from ex

    if not reader.pages:
        raise ValueError(f"PDF file '{filename}' contains 0 pages")

    pages: list[dict[str, Any]] = []
    full_text_parts: list[str] = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        try:
            page_text = page.extract_text() or ""
        except Exception as ex:
            logger.warning("Could not extract text on page %d of '%s': %s", page_num, filename, ex)
            page_text = ""

        cleaned_text = page_text.strip()
        if cleaned_text:
            pages.append({"page": page_num, "text": cleaned_text})
            full_text_parts.append(cleaned_text)

    if not pages:
        raise ValueError(
            f"PDF file '{filename}' has no extractable text. Scanned or image-only PDFs are not supported."
        )

    full_text = "\n\n".join(full_text_parts)
    return full_text, pages


def chunk_pdf_pages(
    pages: list[dict[str, Any]],
    filename: str = "document.pdf",
    chunk_size: int = 700,
    chunk_overlap: int = 100,
) -> list[dict[str, Any]]:
    """Partition extracted PDF pages into chunks with page metadata and overlap.

    Args:
        pages: List of {"page": int, "text": str}.
        filename: Original file name to attach to chunk metadata.
        chunk_size: Maximum character length per chunk.
        chunk_overlap: Overlapping character count across chunks.

    Returns:
        List of dicts: {"chunk_text": str, "metadata": {"page": int, "filename": str, "source_type": "pdf"}}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict[str, Any]] = []
    for page_info in pages:
        page_num = page_info["page"]
        raw_text = page_info["text"]
        sub_chunks = splitter.split_text(raw_text)

        for text in sub_chunks:
            t = text.strip()
            if not t:
                continue
            chunks.append(
                {
                    "chunk_text": t,
                    "metadata": {
                        "page": page_num,
                        "filename": filename,
                        "source_type": "pdf",
                    },
                }
            )

    return chunks


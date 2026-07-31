"""
PDF Service

Responsible for extracting raw text and page-level metadata from PDF files.
Business logic (chunking, embedding) is handled by downstream services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional pypdf import — graceful stub if not installed
# ---------------------------------------------------------------------------
try:
    from pypdf import PdfReader  # type: ignore

    _PYPDF_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYPDF_AVAILABLE = False
    logger.warning(
        "pypdf is not installed. PDF extraction will not work. "
        "Install it with: pip install pypdf"
    )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PageContent:
    """Text and metadata extracted from a single PDF page."""

    page_number: int
    """1-based page number."""

    text: str
    """Raw extracted text (may contain newlines and whitespace artefacts)."""

    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)


@dataclass
class PDFDocument:
    """Aggregated extraction result for an entire PDF file."""

    file_path: Path
    """Absolute path to the source PDF."""

    num_pages: int
    """Total number of pages in the PDF."""

    pages: List[PageContent]
    """Ordered list of extracted pages."""

    title: Optional[str] = None
    """PDF metadata title, if present."""

    author: Optional[str] = None
    """PDF metadata author, if present."""

    @property
    def full_text(self) -> str:
        """Concatenated text of all pages, separated by newlines."""
        return "\n".join(page.text for page in self.pages)

    @property
    def total_chars(self) -> int:
        """Total character count across all pages."""
        return sum(page.char_count for page in self.pages)


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class PDFService:
    """
    Extracts text content and metadata from PDF files.

    Usage::

        service = PDFService()
        doc = service.extract(Path("/uploads/<id>/file.pdf"))
        print(doc.full_text)
    """

    def extract(self, file_path: Path) -> PDFDocument:
        """
        Extract text and metadata from a PDF at *file_path*.

        Args:
            file_path: Absolute path to the PDF file.

        Returns:
            A :class:`PDFDocument` containing per-page text and document metadata.

        Raises:
            FileNotFoundError: If *file_path* does not exist.
            RuntimeError:      If pypdf is not installed or extraction fails.
        """
        if not _PYPDF_AVAILABLE:
            raise RuntimeError(
                "pypdf is required for PDF extraction. "
                "Install it with: pip install pypdf"
            )

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        logger.info("Starting PDF extraction: %s", file_path)

        try:
            reader = PdfReader(str(file_path))
            metadata = reader.metadata or {}

            pages: List[PageContent] = []
            for idx, page in enumerate(reader.pages, start=1):
                raw_text = page.extract_text() or ""
                cleaned = self._clean_text(raw_text)
                pages.append(PageContent(page_number=idx, text=cleaned))

            doc = PDFDocument(
                file_path=file_path,
                num_pages=len(reader.pages),
                pages=pages,
                title=metadata.get("/Title") or None,
                author=metadata.get("/Author") or None,
            )

            logger.info(
                "Extraction complete: %d pages, %d total chars",
                doc.num_pages,
                doc.total_chars,
            )
            return doc

        except Exception as exc:
            logger.exception("PDF extraction failed for '%s': %s", file_path, exc)
            raise RuntimeError(f"Failed to extract PDF '{file_path}': {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Perform lightweight post-processing on raw extracted text.

        - Collapses excessive whitespace / blank lines.
        - Removes null bytes and non-printable control characters.

        Args:
            text: Raw text from pypdf page extraction.

        Returns:
            Cleaned text string.
        """
        import re

        # Remove null bytes and control chars (keep newlines and tabs)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Collapse 3+ consecutive newlines into two
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse multiple spaces/tabs into a single space
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    def get_page_count(self, file_path: Path) -> int:
        """
        Return the number of pages in a PDF without extracting text.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Integer page count.

        Raises:
            RuntimeError: If pypdf is unavailable or the file cannot be read.
        """
        if not _PYPDF_AVAILABLE:
            raise RuntimeError("pypdf is required. Install with: pip install pypdf")
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        reader = PdfReader(str(file_path))
        return len(reader.pages)

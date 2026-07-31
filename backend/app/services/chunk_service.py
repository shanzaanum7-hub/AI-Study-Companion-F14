"""
Chunk Service

Splits extracted PDF text into overlapping token-window chunks that are
sized appropriately for embedding and retrieval.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from app.config import get_settings
from app.services.pdf_service import PDFDocument, PageContent
from app.utils.tokenizer import count_tokens, split_into_token_windows

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TextChunk:
    """A single text chunk ready for embedding."""

    chunk_id: str
    """Globally unique identifier for this chunk (UUID-4 hex)."""

    document_id: uuid.UUID
    """Parent document this chunk belongs to."""

    text: str
    """The raw text content of the chunk."""

    chunk_index: int
    """Zero-based position of this chunk within the document."""

    page_number: Optional[int] = None
    """Source page number (best-effort, may be None for multi-page spans)."""

    token_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.token_count = count_tokens(self.text)


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class ChunkService:
    """
    Splits a :class:`~app.services.pdf_service.PDFDocument` into
    :class:`TextChunk` instances using token-window sliding.

    Args:
        chunk_size:    Target number of tokens per chunk (default from settings).
        chunk_overlap: Number of tokens to overlap between chunks (default from settings).
        model:         Tiktoken encoding name used for token counting.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        model: str = "cl100k_base",
    ) -> None:
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.model = model

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_document(
        self,
        document: PDFDocument,
        document_id: uuid.UUID,
    ) -> List[TextChunk]:
        """
        Split every page of *document* into token-windowed chunks.

        Pages are processed individually so that chunk boundaries respect
        page boundaries wherever possible. Very long pages are windowed;
        very short pages may produce a single chunk or be merged with
        adjacent pages via :meth:`chunk_full_text`.

        Args:
            document:    Extracted PDF document.
            document_id: UUID to associate with every produced chunk.

        Returns:
            Ordered list of :class:`TextChunk` objects.
        """
        logger.info(
            "Chunking document %s: %d pages, chunk_size=%d, overlap=%d",
            document_id,
            document.num_pages,
            self.chunk_size,
            self.chunk_overlap,
        )

        all_chunks: List[TextChunk] = []
        global_index = 0

        for page in document.pages:
            page_chunks = self._chunk_page(page, document_id, global_index)
            all_chunks.extend(page_chunks)
            global_index += len(page_chunks)

        logger.info(
            "Produced %d chunks for document %s", len(all_chunks), document_id
        )
        return all_chunks

    def chunk_text(
        self,
        text: str,
        document_id: uuid.UUID,
        page_number: Optional[int] = None,
    ) -> List[TextChunk]:
        """
        Split an arbitrary text string into token-windowed chunks.

        Useful when a pre-extracted string is available rather than a full
        :class:`PDFDocument`.

        Args:
            text:        Raw text to chunk.
            document_id: Parent document UUID.
            page_number: Optional source page to stamp on every chunk.

        Returns:
            Ordered list of :class:`TextChunk` objects.
        """
        windows = split_into_token_windows(
            text,
            window_size=self.chunk_size,
            overlap=self.chunk_overlap,
            model=self.model,
        )

        chunks: List[TextChunk] = []
        for idx, window_text in enumerate(windows):
            if not window_text.strip():
                continue
            chunks.append(
                TextChunk(
                    chunk_id=self._new_chunk_id(),
                    document_id=document_id,
                    text=window_text,
                    chunk_index=idx,
                    page_number=page_number,
                )
            )
        return chunks

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _chunk_page(
        self,
        page: PageContent,
        document_id: uuid.UUID,
        start_index: int,
    ) -> List[TextChunk]:
        """Chunk a single page and return its TextChunk list."""
        if not page.text.strip():
            logger.debug("Skipping empty page %d", page.page_number)
            return []

        windows = split_into_token_windows(
            page.text,
            window_size=self.chunk_size,
            overlap=self.chunk_overlap,
            model=self.model,
        )

        chunks: List[TextChunk] = []
        for offset, window_text in enumerate(windows):
            if not window_text.strip():
                continue
            chunks.append(
                TextChunk(
                    chunk_id=self._new_chunk_id(),
                    document_id=document_id,
                    text=window_text,
                    chunk_index=start_index + offset,
                    page_number=page.page_number,
                )
            )
        return chunks

    @staticmethod
    def _new_chunk_id() -> str:
        """Generate a new UUID-4 hex string for a chunk."""
        return uuid.uuid4().hex

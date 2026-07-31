"""
Retrieval Service

Orchestrates semantic search: embeds a query, searches Qdrant, and maps
raw vector results back to typed :class:`ChunkResult` objects.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from app.config import get_settings
from app.models.response_models import ChunkResult
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService, VectorSearchResult

logger = logging.getLogger(__name__)
settings = get_settings()


class RetrievalService:
    """
    Combines embedding and vector search into a single high-level API.

    Args:
        embedding_service: An :class:`EmbeddingService` instance.
        qdrant_service:    A :class:`QdrantService` instance.
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        qdrant_service: Optional[QdrantService] = None,
    ) -> None:
        self._embedder = embedding_service or EmbeddingService()
        self._qdrant = qdrant_service or QdrantService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        document_ids: Optional[List[uuid.UUID]] = None,
        subject: Optional[str] = None,
    ) -> List[ChunkResult]:
        """
        Embed *query* and return the most relevant text chunks.

        Args:
            query:           Natural-language search query.
            top_k:           Max number of results (default from settings).
            score_threshold: Min similarity score (default from settings).
            document_ids:    Restrict results to these document IDs.
            subject:         Restrict results to this subject tag.

        Returns:
            List of :class:`ChunkResult` sorted by descending similarity score.
        """
        if not query.strip():
            logger.warning("Empty query received; returning empty results.")
            return []

        logger.info("Retrieval search: query=%r, top_k=%s", query[:80], top_k)

        # 1. Embed the query
        query_vector = self._embedder.embed_text(query)

        # 2. Search Qdrant
        raw_results: List[VectorSearchResult] = self._qdrant.search(
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            filter_document_ids=document_ids,
            filter_subject=subject,
        )

        # 3. Map to typed response models
        chunk_results = [self._to_chunk_result(r) for r in raw_results]

        logger.info(
            "Retrieval returned %d chunk(s) for query=%r",
            len(chunk_results),
            query[:80],
        )
        return chunk_results

    def index_chunks(
        self,
        texts: List[str],
        payloads: List[dict],
        chunk_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Embed a list of text chunks and upsert them into Qdrant.

        Args:
            texts:     Raw text strings to embed and store.
            payloads:  Metadata dicts (must include at minimum ``document_id``
                       and ``chunk_index``).
            chunk_ids: Optional explicit IDs; auto-generated if None.

        Raises:
            ValueError: If *texts* and *payloads* have different lengths.
        """
        if len(texts) != len(payloads):
            raise ValueError("texts and payloads must have the same length.")

        if not texts:
            logger.debug("index_chunks called with empty list; nothing to do.")
            return

        logger.info("Indexing %d chunk(s) into Qdrant.", len(texts))

        # Ensure collection exists before upserting
        self._qdrant.ensure_collection()

        # Embed in one batched call
        vectors = self._embedder.embed_batch(texts)

        # Upsert
        self._qdrant.upsert_vectors(
            vectors=vectors,
            payloads=payloads,
            ids=chunk_ids,
        )

        logger.info("Indexed %d chunk(s) successfully.", len(texts))

    def delete_document(self, document_id: uuid.UUID) -> None:
        """
        Remove all indexed chunks that belong to *document_id*.

        Args:
            document_id: UUID of the document to remove from the index.
        """
        logger.info("Deleting indexed chunks for document %s.", document_id)
        self._qdrant.delete_by_document_id(document_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_chunk_result(result: VectorSearchResult) -> ChunkResult:
        """
        Map a raw :class:`VectorSearchResult` to a :class:`ChunkResult`.

        Args:
            result: Raw search result from Qdrant.

        Returns:
            Typed :class:`ChunkResult` for API responses.
        """
        payload = result.payload

        # document_id stored as string in Qdrant payload
        raw_doc_id = payload.get("document_id", "")
        try:
            document_id = uuid.UUID(str(raw_doc_id))
        except (ValueError, AttributeError):
            document_id = uuid.UUID(int=0)  # fallback sentinel

        return ChunkResult(
            chunk_id=result.id,
            document_id=document_id,
            document_title=payload.get("document_title"),
            text=payload.get("text", ""),
            score=round(result.score, 6),
            page_number=payload.get("page_number"),
            chunk_index=payload.get("chunk_index", 0),
        )

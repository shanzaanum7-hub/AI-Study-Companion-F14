"""
Retrieval Service

Orchestrates the full semantic search pipeline:

    user query
        │
        ▼
    generate_query_embedding()   ← embedding_service (Gemini)
        │
        ▼
    retrieve_vectors()           ← qdrant_service (cosine similarity)
        │
        ▼
    List[SimpleRetrieveResult]   ← typed response models

This module is the only place that knows about both the embedding service
and the vector DB service. Routers depend solely on this class.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from app.config import get_settings
from app.models.response_models import ChunkResult, SimpleRetrieveResult
from app.services import embedding_service as emb
from app.services import qdrant_service as qdrant
from app.services.embedding_service import (
    EmbeddingServiceError,
    InvalidAPIKeyError,
    RateLimitError,
    EmbeddingTimeoutError,
)
from app.services.qdrant_service import (
    QdrantConnectionError,
    QdrantDimensionMismatchError,
    QdrantServiceError,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Domain-level exceptions — routers catch these and map to HTTP status codes
# ---------------------------------------------------------------------------


class RetrievalError(Exception):
    """Base class for all retrieval pipeline errors."""


class RetrievalEmbeddingError(RetrievalError):
    """Raised when the embedding step fails (bad key, timeout, rate-limit)."""


class RetrievalDatabaseError(RetrievalError):
    """Raised when the Qdrant search step fails (connection refused, etc.)."""


class RetrievalConfigError(RetrievalError):
    """Raised for configuration problems (missing API key, wrong dimension)."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class RetrievalService:
    """
    High-level retrieval orchestrator.

    All public methods return plain Python types (lists of Pydantic models)
    so that routers need no knowledge of Qdrant or Gemini internals.

    Usage::

        svc = RetrievalService()
        results = svc.retrieve("CPU Scheduling", top_k=5)
    """

    # ------------------------------------------------------------------
    # Primary API — used by POST /api/retrieve
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        document_id: Optional[str] = None,
    ) -> List[SimpleRetrieveResult]:
        """
        Run the full semantic search pipeline for a user query.

        Steps:
          1. Validate and sanitise the query string.
          2. Generate a Gemini query embedding.
          3. Search Qdrant with cosine similarity.
          4. Map raw hits to typed :class:`SimpleRetrieveResult` objects.

        Args:
            query:           Natural-language search string.
            top_k:           Maximum number of results to return (1–20).
            score_threshold: Optional minimum similarity score (0.0–1.0).
                             When None, Qdrant returns the top-k regardless
                             of absolute score.
            document_id:     Restrict search to a single document's chunks.

        Returns:
            List of :class:`SimpleRetrieveResult` sorted by descending score.
            An empty list is returned when the index contains no matching chunks
            (not an error — the router maps this to a 404 response).

        Raises:
            RetrievalConfigError:   Missing / invalid API key or dimension mismatch.
            RetrievalEmbeddingError: Gemini rate-limit, timeout, or unknown API error.
            RetrievalDatabaseError:  Qdrant unreachable or query rejected.
        """
        query = query.strip()
        if not query:
            logger.warning("retrieve() called with blank query — returning empty list.")
            return []

        logger.info(
            "Retrieval pipeline start | query=%r | top_k=%d | threshold=%s | doc_id=%s",
            query[:80],
            top_k,
            score_threshold,
            document_id,
        )

        # ── Step 1: Embed the query ──────────────────────────────────────
        query_vector = self._embed_query(query)

        # ── Step 2: Search Qdrant ────────────────────────────────────────
        raw_hits = self._search_qdrant(
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            document_id=document_id,
        )

        # ── Step 3: Map to response models ───────────────────────────────
        results = [self._to_simple_result(hit) for hit in raw_hits]

        logger.info(
            "Retrieval pipeline end | query=%r | returned=%d chunk(s)",
            query[:80],
            len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Extended API — used by /retrieval/search and /retrieval/ask
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
        Richer search that returns full :class:`ChunkResult` objects.

        Used by the existing /retrieval/search and /retrieval/ask endpoints.
        Delegates to :meth:`retrieve` then re-maps to the heavier model.

        Args:
            query:           Search query string.
            top_k:           Max results (falls back to settings.RETRIEVAL_TOP_K).
            score_threshold: Min similarity score.
            document_ids:    Restrict to these document UUIDs.
            subject:         (Not yet filterable at Qdrant level — ignored for now.)

        Returns:
            List of :class:`ChunkResult` sorted by descending score.
        """
        k = top_k or settings.RETRIEVAL_TOP_K

        # Use the first document_id if multiple were supplied — the simple
        # qdrant_service layer only accepts a single string filter right now.
        doc_id_str: Optional[str] = None
        if document_ids:
            doc_id_str = str(document_ids[0])
            if len(document_ids) > 1:
                logger.warning(
                    "search() received %d document_ids but the current qdrant_service "
                    "implementation supports a single filter. Using %s only.",
                    len(document_ids),
                    doc_id_str,
                )

        simple_results = self.retrieve(
            query=query,
            top_k=k,
            score_threshold=score_threshold,
            document_id=doc_id_str,
        )
        return [self._simple_to_chunk_result(r) for r in simple_results]

    def index_chunks(
        self,
        texts: List[str],
        payloads: List[dict],
        chunk_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Embed a batch of text chunks and upsert them into Qdrant.

        Args:
            texts:     Raw text strings to embed.
            payloads:  Metadata dicts — must include at minimum
                       ``document_id``, ``chunk_id``, and ``text``.
            chunk_ids: Optional explicit chunk IDs (ignored; IDs live in payload).

        Raises:
            ValueError: If ``texts`` and ``payloads`` have different lengths.
        """
        if len(texts) != len(payloads):
            raise ValueError("texts and payloads must have the same length.")
        if not texts:
            logger.debug("index_chunks called with empty list — nothing to do.")
            return

        logger.info("Indexing %d chunk(s) into Qdrant.", len(texts))

        # Build the list of dicts that qdrant_service.store_vectors() expects
        items = []
        for text, payload in zip(texts, payloads):
            # Generate embedding for each chunk using the document task_type
            try:
                embedding = emb._embed_with_retry(text, task_type="retrieval_document")
            except EmbeddingServiceError as exc:
                raise RetrievalEmbeddingError(
                    f"Embedding failed for chunk {payload.get('chunk_id')}: {exc}"
                ) from exc

            items.append(
                {
                    "document_id": str(payload.get("document_id", "")),
                    "chunk_id": str(payload.get("chunk_id", "")),
                    "text": text,
                    "embedding": embedding,
                }
            )

        try:
            qdrant.store_vectors(items)
        except QdrantConnectionError as exc:
            raise RetrievalDatabaseError(str(exc)) from exc
        except QdrantServiceError as exc:
            raise RetrievalDatabaseError(str(exc)) from exc

        logger.info("Indexed %d chunk(s) successfully.", len(texts))

    def delete_document(self, document_id: uuid.UUID) -> None:
        """
        Remove all indexed chunks that belong to *document_id*.

        Args:
            document_id: UUID of the document to purge from the index.
        """
        logger.info("Deleting indexed chunks for document %s.", document_id)
        try:
            qdrant.delete_document_vectors(str(document_id))
        except QdrantConnectionError as exc:
            raise RetrievalDatabaseError(str(exc)) from exc
        except QdrantServiceError as exc:
            raise RetrievalDatabaseError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _embed_query(self, query: str) -> List[float]:
        """
        Generate a Gemini embedding for the query string.

        Wraps embedding-layer exceptions in domain-level errors so
        the router only needs to handle :class:`RetrievalError` subtypes.

        Raises:
            RetrievalConfigError:   Invalid / missing API key.
            RetrievalEmbeddingError: Rate-limit, timeout, or generic API error.
        """
        try:
            vector = emb.generate_query_embedding(query)
            logger.debug(
                "Query embedded | dim=%d | query=%r", len(vector), query[:60]
            )
            return vector
        except InvalidAPIKeyError as exc:
            raise RetrievalConfigError(
                "Gemini API key is missing or invalid. "
                "Set GEMINI_API_KEY in your .env file."
            ) from exc
        except RateLimitError as exc:
            raise RetrievalEmbeddingError(
                "Embedding service rate limit exceeded. Please retry in a moment."
            ) from exc
        except EmbeddingTimeoutError as exc:
            raise RetrievalEmbeddingError(
                "Embedding service timed out. Please retry."
            ) from exc
        except EmbeddingServiceError as exc:
            raise RetrievalEmbeddingError(
                f"Embedding generation failed: {exc}"
            ) from exc

    def _search_qdrant(
        self,
        query_vector: List[float],
        top_k: int,
        score_threshold: Optional[float],
        document_id: Optional[str],
    ) -> List[dict]:
        """
        Run a cosine similarity search against Qdrant.

        Raises:
            RetrievalConfigError:  Vector dimension mismatch.
            RetrievalDatabaseError: Connection failure or server-side error.
        """
        try:
            hits = qdrant.retrieve_vectors(
                query_embedding=query_vector,
                top_k=top_k,
                score_threshold=score_threshold,
                document_id=document_id,
            )
            logger.debug(
                "Qdrant search complete | hits=%d | top_k=%d", len(hits), top_k
            )
            return hits
        except QdrantDimensionMismatchError as exc:
            raise RetrievalConfigError(
                f"Embedding dimension mismatch between query vector and Qdrant collection: {exc}"
            ) from exc
        except QdrantConnectionError as exc:
            raise RetrievalDatabaseError(
                "Cannot reach the Qdrant vector database. "
                f"Make sure Qdrant is running at {qdrant.QDRANT_URL}."
            ) from exc
        except QdrantServiceError as exc:
            raise RetrievalDatabaseError(
                f"Qdrant search failed: {exc}"
            ) from exc

    @staticmethod
    def _to_simple_result(hit: dict) -> SimpleRetrieveResult:
        """
        Map a raw Qdrant hit dict to a :class:`SimpleRetrieveResult`.

        The ``score`` field is clamped to [0, 1] because cosine similarity
        returned by Qdrant is already normalised, but rounding can push
        it marginally outside the valid range.

        Args:
            hit: Dict from :func:`qdrant_service.retrieve_vectors` with keys
                 ``score``, ``text``, ``chunk_id``, ``document_id``.

        Returns:
            Typed :class:`SimpleRetrieveResult`.
        """
        raw_score = hit.get("score", 0.0)
        score = max(0.0, min(1.0, round(float(raw_score), 6)))

        return SimpleRetrieveResult(
            score=score,
            text=hit.get("text") or "",
            chunk_id=hit.get("chunk_id"),
            document_id=hit.get("document_id"),
            page_number=hit.get("page_number"),  # present when upload pipeline sets it
        )

    @staticmethod
    def _simple_to_chunk_result(r: SimpleRetrieveResult) -> ChunkResult:
        """
        Upcast a :class:`SimpleRetrieveResult` to a full :class:`ChunkResult`.

        Used by :meth:`search` so the /retrieval/search and /retrieval/ask
        endpoints continue to return the richer model they already declare.
        """
        try:
            doc_uuid = uuid.UUID(r.document_id) if r.document_id else uuid.UUID(int=0)
        except (ValueError, AttributeError):
            doc_uuid = uuid.UUID(int=0)

        return ChunkResult(
            chunk_id=r.chunk_id or "",
            document_id=doc_uuid,
            document_title=None,
            text=r.text,
            score=r.score,
            page_number=r.page_number,
            chunk_index=0,
        )

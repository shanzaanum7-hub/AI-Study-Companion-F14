"""
Qdrant Service

Manages all interactions with the Qdrant vector database:
  - Collection lifecycle (create, check, delete)
  - Upsert / delete vectors
  - Similarity search
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Optional qdrant-client import
# ---------------------------------------------------------------------------
try:
    from qdrant_client import QdrantClient  # type: ignore
    from qdrant_client.http import models as qmodels  # type: ignore

    _QDRANT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _QDRANT_AVAILABLE = False
    logger.warning(
        "qdrant-client is not installed. Vector storage will not work. "
        "Install with: pip install qdrant-client"
    )


# ---------------------------------------------------------------------------
# Data class for search results
# ---------------------------------------------------------------------------


class VectorSearchResult:
    """Represents a single result from a Qdrant similarity search."""

    __slots__ = ("id", "score", "payload")

    def __init__(self, id: str, score: float, payload: Dict[str, Any]) -> None:
        self.id = id
        self.score = score
        self.payload = payload

    def __repr__(self) -> str:  # pragma: no cover
        return f"VectorSearchResult(id={self.id!r}, score={self.score:.4f})"


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class QdrantService:
    """
    Thin wrapper around the Qdrant Python client.

    Provides collection management and vector CRUD operations.
    All methods log at DEBUG/INFO level and propagate exceptions to callers.

    Args:
        collection_name: Qdrant collection to operate on (default from settings).
        vector_size:     Dimensionality of stored vectors (default from settings).
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        vector_size: Optional[int] = None,
    ) -> None:
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.vector_size = vector_size or settings.EMBEDDING_DIMENSION
        self._client: Optional["QdrantClient"] = None

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    @property
    def client(self) -> "QdrantClient":
        """Return a lazy-initialised Qdrant client."""
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> "QdrantClient":
        """Instantiate and return a QdrantClient."""
        if not _QDRANT_AVAILABLE:
            raise RuntimeError(
                "qdrant-client is required. Install with: pip install qdrant-client"
            )
        logger.info(
            "Connecting to Qdrant at %s:%d", settings.QDRANT_HOST, settings.QDRANT_PORT
        )
        return QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY,
            prefer_grpc=False,
        )

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def ensure_collection(self) -> None:
        """
        Create the collection if it does not already exist.

        Uses cosine distance and the configured vector size.
        """
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name in existing:
            logger.debug("Collection '%s' already exists.", self.collection_name)
            return

        logger.info(
            "Creating Qdrant collection '%s' (dim=%d)",
            self.collection_name,
            self.vector_size,
        )
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=qmodels.VectorParams(
                size=self.vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info("Collection '%s' created.", self.collection_name)

    def collection_exists(self) -> bool:
        """Return True if the collection exists in Qdrant."""
        collections = [c.name for c in self.client.get_collections().collections]
        return self.collection_name in collections

    def delete_collection(self) -> None:
        """Delete the collection and all its vectors (irreversible)."""
        if self.collection_exists():
            self.client.delete_collection(self.collection_name)
            logger.info("Collection '%s' deleted.", self.collection_name)

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Return basic stats about the collection.

        Returns:
            Dict with keys: name, vectors_count, status.
        """
        info = self.client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "vectors_count": info.vectors_count,
            "status": str(info.status),
        }

    # ------------------------------------------------------------------
    # Vector CRUD
    # ------------------------------------------------------------------

    def upsert_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Upsert a batch of vectors with associated payloads.

        Args:
            vectors:  List of embedding vectors (each a list of floats).
            payloads: List of metadata dicts, one per vector.
            ids:      Optional list of string IDs; auto-generated if None.

        Raises:
            ValueError: If lengths of vectors and payloads differ.
        """
        if len(vectors) != len(payloads):
            raise ValueError("vectors and payloads must have the same length.")

        point_ids = ids or [uuid.uuid4().hex for _ in vectors]

        points = [
            qmodels.PointStruct(id=pid, vector=vec, payload=pay)
            for pid, vec, pay in zip(point_ids, vectors, payloads)
        ]

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.debug(
            "Upserted %d vectors into collection '%s'.",
            len(points),
            self.collection_name,
        )

    def delete_by_document_id(self, document_id: uuid.UUID) -> None:
        """
        Delete all vectors whose payload contains the given document_id.

        Args:
            document_id: UUID of the document whose chunks should be removed.
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
        )
        logger.info(
            "Deleted vectors for document_id '%s' from collection '%s'.",
            document_id,
            self.collection_name,
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_vector: List[float],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter_document_ids: Optional[List[uuid.UUID]] = None,
        filter_subject: Optional[str] = None,
    ) -> List[VectorSearchResult]:
        """
        Perform a cosine similarity search.

        Args:
            query_vector:        Embedding of the search query.
            top_k:               Max results to return (default from settings).
            score_threshold:     Min similarity score (default from settings).
            filter_document_ids: Restrict to these document IDs (optional).
            filter_subject:      Restrict to this subject tag (optional).

        Returns:
            List of :class:`VectorSearchResult`, sorted by descending score.
        """
        k = top_k or settings.RETRIEVAL_TOP_K
        threshold = score_threshold if score_threshold is not None else settings.RETRIEVAL_SCORE_THRESHOLD

        must_conditions: List[Any] = []

        if filter_document_ids:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchAny(
                        any=[str(did) for did in filter_document_ids]
                    ),
                )
            )

        if filter_subject:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="subject",
                    match=qmodels.MatchValue(value=filter_subject),
                )
            )

        query_filter = qmodels.Filter(must=must_conditions) if must_conditions else None

        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=k,
            score_threshold=threshold,
            query_filter=query_filter,
            with_payload=True,
        )

        results = [
            VectorSearchResult(id=str(hit.id), score=hit.score, payload=hit.payload or {})
            for hit in hits
        ]

        logger.debug(
            "Search returned %d results (top_k=%d, threshold=%.2f).",
            len(results),
            k,
            threshold,
        )
        return results

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """
        Check connectivity to the Qdrant server.

        Returns:
            True if reachable, False otherwise.
        """
        try:
            self.client.get_collections()
            return True
        except Exception as exc:
            logger.warning("Qdrant ping failed: %s", exc)
            return False

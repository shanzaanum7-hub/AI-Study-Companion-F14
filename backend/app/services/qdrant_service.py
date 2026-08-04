"""
qdrant_service.py
------------------
Handles all interaction with the Qdrant Vector Database.

Responsibilities:
- Auto-create the "study_notes" collection if it doesn't exist.
- Store vectors (id, document_id, chunk_id, text, embedding).
- Retrieve vectors (similarity search).
- Delete vectors belonging to a document.

Follows clean architecture: this module only knows about Qdrant.
Callers (routers/other services) should not import qdrant_client directly.
"""

import os
import logging
import uuid
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (read from .env)
# ---------------------------------------------------------------------------
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_URL = os.getenv("QDRANT_URL") or f"http://{QDRANT_HOST}:{QDRANT_PORT}"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # optional, e.g. for Qdrant Cloud

# NOTE: This is a DIFFERENT collection from QDRANT_COLLECTION_NAME (used by the
# 384-dim sentence-transformers pipeline elsewhere in the project). Keep them separate.
QDRANT_COLLECTION_NAME = os.getenv("STUDY_NOTES_COLLECTION", "study_notes")

# Gemini text-embedding-004 = 768 dimensions (different from the 384-dim
# sentence-transformers model used elsewhere in the project).
EMBEDDING_VECTOR_SIZE = int(os.getenv("GEMINI_EMBEDDING_DIMENSION", 768))
QDRANT_DISTANCE_METRIC = os.getenv("QDRANT_DISTANCE_METRIC", "Cosine")


class QdrantServiceError(Exception):
    """Base exception for Qdrant service errors."""


class QdrantConnectionError(QdrantServiceError):
    """Raised when Qdrant cannot be reached (connection refused, host down, etc.)."""


class QdrantDimensionMismatchError(QdrantServiceError):
    """Raised when the embedding size doesn't match the collection's vector size."""


class QdrantCollectionError(QdrantServiceError):
    """Raised for collection-related errors (creation/check failures)."""


_client: Optional[QdrantClient] = None


def _get_client() -> QdrantClient:
    """Lazily create and cache a QdrantClient instance."""
    global _client
    if _client is None:
        try:
            _client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=10,
            )
        except Exception as e:
            raise QdrantConnectionError(
                f"Could not create Qdrant client for {QDRANT_URL}: {e}"
            ) from e
    return _client


def _distance_enum() -> qmodels.Distance:
    mapping = {
        "cosine": qmodels.Distance.COSINE,
        "euclid": qmodels.Distance.EUCLID,
        "dot": qmodels.Distance.DOT,
    }
    return mapping.get(QDRANT_DISTANCE_METRIC.lower(), qmodels.Distance.COSINE)


def ensure_collection_exists(vector_size: int = EMBEDDING_VECTOR_SIZE) -> None:
    """
    Check if the study_notes collection exists; create it if not.
    Safe to call multiple times.
    """
    client = _get_client()

    try:
        exists = client.collection_exists(QDRANT_COLLECTION_NAME)
    except (httpx.ConnectError, ConnectionRefusedError) as e:
        raise QdrantConnectionError(
            f"Cannot connect to Qdrant at {QDRANT_URL}. Is it running? Details: {e}"
        ) from e
    except Exception as e:
        raise QdrantCollectionError(f"Error checking collection existence: {e}") from e

    if exists:
        logger.info("Qdrant collection '%s' already exists.", QDRANT_COLLECTION_NAME)
        return

    try:
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=_distance_enum(),
            ),
        )
        logger.info("Created Qdrant collection '%s'.", QDRANT_COLLECTION_NAME)
    except Exception as e:
        raise QdrantCollectionError(
            f"Failed to create collection '{QDRANT_COLLECTION_NAME}': {e}"
        ) from e


def store_vectors(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Store chunk vectors in Qdrant.

    Args:
        items: List of dicts, each containing:
            {
                "document_id": str,
                "chunk_id": str,
                "text": str,
                "embedding": List[float]
            }

    Returns:
        {"status": "success", "count": <int>}
    """
    if not items:
        return {"status": "success", "count": 0}

    ensure_collection_exists(vector_size=len(items[0]["embedding"]))

    client = _get_client()
    points = []

    for item in items:
        embedding = item.get("embedding")
        if embedding is None:
            raise QdrantServiceError(f"Missing embedding for chunk {item.get('chunk_id')}")

        if len(embedding) != EMBEDDING_VECTOR_SIZE:
            raise QdrantDimensionMismatchError(
                f"Embedding size {len(embedding)} does not match expected "
                f"collection size {EMBEDDING_VECTOR_SIZE} for chunk {item.get('chunk_id')}."
            )

        point_id = str(uuid.uuid4())
        points.append(
            qmodels.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "document_id": item.get("document_id"),
                    "chunk_id": item.get("chunk_id"),
                    "text": item.get("text"),
                },
            )
        )

    try:
        client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)
    except UnexpectedResponse as e:
        # e.g. dimension mismatch reported by the server itself
        if "dimension" in str(e).lower():
            raise QdrantDimensionMismatchError(
                f"Qdrant rejected the upsert due to a vector dimension mismatch: {e}"
            ) from e
        raise QdrantServiceError(f"Qdrant upsert failed: {e}") from e
    except (httpx.ConnectError, ConnectionRefusedError) as e:
        raise QdrantConnectionError(
            f"Cannot connect to Qdrant at {QDRANT_URL} while storing vectors: {e}"
        ) from e

    return {"status": "success", "count": len(points)}


def retrieve_vectors(
    query_embedding: List[float],
    top_k: int = 5,
    score_threshold: Optional[float] = None,
    document_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most similar chunks to a query embedding.

    Args:
        query_embedding: Embedding vector of the user query.
        top_k: Number of results to return.
        score_threshold: Minimum similarity score to include a result.
        document_id: Optional filter to search within a single document.

    Returns:
        List of dicts: [{"chunk_id", "document_id", "text", "score"}]
    """
    ensure_collection_exists(vector_size=len(query_embedding))

    client = _get_client()

    query_filter = None
    if document_id:
        query_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchValue(value=document_id),
                )
            ]
        )

    try:
        results = client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )
    except UnexpectedResponse as e:
        if "dimension" in str(e).lower():
            raise QdrantDimensionMismatchError(
                f"Query embedding dimension does not match collection: {e}"
            ) from e
        raise QdrantServiceError(f"Qdrant search failed: {e}") from e
    except (httpx.ConnectError, ConnectionRefusedError) as e:
        raise QdrantConnectionError(
            f"Cannot connect to Qdrant at {QDRANT_URL} while searching: {e}"
        ) from e

    return [
        {
            "chunk_id": hit.payload.get("chunk_id"),
            "document_id": hit.payload.get("document_id"),
            "text": hit.payload.get("text"),
            "score": hit.score,
        }
        for hit in results
    ]


def delete_document_vectors(document_id: str) -> Dict[str, Any]:
    """
    Delete all vectors belonging to a specific document.

    Args:
        document_id: The document whose chunks should be removed.

    Returns:
        {"status": "success", "document_id": document_id}
    """
    if not document_id:
        raise ValueError("document_id must be provided.")

    client = _get_client()

    try:
        client.delete(
            collection_name=QDRANT_COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
    except (httpx.ConnectError, ConnectionRefusedError) as e:
        raise QdrantConnectionError(
            f"Cannot connect to Qdrant at {QDRANT_URL} while deleting vectors: {e}"
        ) from e
    except Exception as e:
        raise QdrantServiceError(
            f"Failed to delete vectors for document {document_id}: {e}"
        ) from e

    return {"status": "success", "document_id": document_id}
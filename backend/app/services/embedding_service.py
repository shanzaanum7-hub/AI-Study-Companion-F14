"""
embedding_service.py
---------------------
Handles embedding generation using the Google Gemini Embedding API.

Responsibilities:
- Generate embeddings for document chunks.
- Generate embeddings for user queries.
- Handle API timeouts, invalid API keys, and rate limits with retries.

No API keys are hardcoded — everything is read from environment variables (.env).
"""

import os
import time
import logging
from typing import List, Dict, Any

import google.generativeai as genai
from google.api_core.exceptions import (
    ResourceExhausted,
    DeadlineExceeded,
    Unauthenticated,
    PermissionDenied,
    ServiceUnavailable,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (read from .env)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
# Kept in sync with GEMINI_EMBEDDING_DIMENSION in .env — used by qdrant_service.py
GEMINI_EMBEDDING_DIMENSION = int(os.getenv("GEMINI_EMBEDDING_DIMENSION", 768))

MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", 3))
RETRY_BACKOFF_SECONDS = float(os.getenv("EMBEDDING_RETRY_BACKOFF", 2))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("EMBEDDING_TIMEOUT", 30))


class EmbeddingServiceError(Exception):
    """Base exception for embedding service errors."""


class InvalidAPIKeyError(EmbeddingServiceError):
    """Raised when the Gemini API key is missing or invalid."""


class RateLimitError(EmbeddingServiceError):
    """Raised when the Gemini API rate limit is hit and retries are exhausted."""


class EmbeddingTimeoutError(EmbeddingServiceError):
    """Raised when the Gemini API call times out repeatedly."""


def _configure_client() -> None:
    """Configure the Gemini client. Raises InvalidAPIKeyError if key is missing."""
    if not GEMINI_API_KEY:
        raise InvalidAPIKeyError(
            "GEMINI_API_KEY is not set. Please add it to your .env file."
        )
    genai.configure(api_key=GEMINI_API_KEY)


def _embed_with_retry(text: str, task_type: str) -> List[float]:
    """
    Call the Gemini embedding API with retry logic for transient failures.

    task_type: "retrieval_document" for chunks, "retrieval_query" for queries.
    """
    _configure_client()

    last_exception: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = genai.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type=task_type,
                request_options={"timeout": REQUEST_TIMEOUT_SECONDS},
            )
            embedding = response.get("embedding")
            if not embedding:
                raise EmbeddingServiceError("Gemini API returned an empty embedding.")
            return embedding

        except (Unauthenticated, PermissionDenied) as e:
            # Invalid API key — no point retrying.
            raise InvalidAPIKeyError(f"Invalid or unauthorized Gemini API key: {e}") from e

        except ResourceExhausted as e:
            # Rate limit hit — retry with backoff.
            last_exception = e
            logger.warning(
                "Gemini rate limit hit (attempt %s/%s). Retrying...", attempt, MAX_RETRIES
            )
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        except (DeadlineExceeded, ServiceUnavailable, TimeoutError) as e:
            # Timeout / transient outage — retry with backoff.
            last_exception = e
            logger.warning(
                "Gemini request timeout/unavailable (attempt %s/%s). Retrying...",
                attempt,
                MAX_RETRIES,
            )
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        except Exception as e:
            # Unknown error — do not silently retry forever, but allow one retry pass.
            last_exception = e
            logger.error("Unexpected error from Gemini API: %s", e)
            time.sleep(RETRY_BACKOFF_SECONDS)

    # Retries exhausted
    if isinstance(last_exception, ResourceExhausted):
        raise RateLimitError(
            f"Gemini API rate limit exceeded after {MAX_RETRIES} attempts."
        ) from last_exception
    if isinstance(last_exception, (DeadlineExceeded, TimeoutError, ServiceUnavailable)):
        raise EmbeddingTimeoutError(
            f"Gemini API timed out after {MAX_RETRIES} attempts."
        ) from last_exception

    raise EmbeddingServiceError(
        f"Failed to generate embedding after {MAX_RETRIES} attempts: {last_exception}"
    )


def generate_chunk_embeddings(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate embeddings for a list of document chunks.

    Args:
        chunks: List of dicts, each containing at least:
            {"chunk_id": str, "text": str}

    Returns:
        List of dicts in the form:
            [{"chunk_id": "...", "embedding": [...]}]
    """
    results: List[Dict[str, Any]] = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        text = chunk.get("text", "")

        if not chunk_id or not text.strip():
            logger.warning("Skipping chunk with missing id or empty text: %s", chunk)
            continue

        try:
            embedding = _embed_with_retry(text, task_type="retrieval_document")
            results.append({"chunk_id": chunk_id, "embedding": embedding})
        except EmbeddingServiceError as e:
            logger.error("Failed to embed chunk %s: %s", chunk_id, e)
            # Re-raise so the caller (e.g. upload pipeline) knows something failed.
            raise

    return results


def generate_query_embedding(query: str) -> List[float]:
    """
    Generate an embedding for a single user query.

    Args:
        query: The user's search/question text.

    Returns:
        A list of floats representing the query embedding.
    """
    if not query or not query.strip():
        raise ValueError("Query text must not be empty.")

    return _embed_with_retry(query, task_type="retrieval_query")
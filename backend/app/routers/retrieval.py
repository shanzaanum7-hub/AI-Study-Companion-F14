"""
Retrieval Router

Endpoints
─────────
POST /api/retrieve          Simple semantic search  ← primary new endpoint
POST /api/v1/retrieval/search   Full search with filters (existing)
POST /api/v1/retrieval/ask      RAG question answering (existing)

HTTP status codes
─────────────────
200  Matching chunks returned
404  Query was valid but the index returned zero results
422  Request body failed Pydantic validation  (FastAPI automatic)
500  Unexpected / unclassified server error
503  Upstream dependency unavailable (Qdrant down, Gemini unreachable)
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.models.response_models import (
    AnswerResponse,
    APIResponse,
    RetrievalResponse,
    SimpleRetrieveResponse,
)
from app.models.schemas import AskQuestionSchema, RetrievalQuerySchema, SimpleRetrieveSchema
from app.services.retrieval_service import (
    RetrievalConfigError,
    RetrievalDatabaseError,
    RetrievalEmbeddingError,
    RetrievalService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Retrieval"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def get_retrieval_service() -> RetrievalService:
    """Provide a per-request RetrievalService instance."""
    return RetrievalService()


def get_settings_dep() -> Settings:
    return get_settings()


# ---------------------------------------------------------------------------
# Shared error-mapping helper
# ---------------------------------------------------------------------------


def _handle_retrieval_error(exc: Exception) -> JSONResponse:
    """
    Map domain-level RetrievalError subtypes to the correct HTTP status and
    a consistent JSON envelope.

    Called from every endpoint's except block so the mapping lives in one place.
    """
    if isinstance(exc, RetrievalConfigError):
        logger.error("Retrieval config error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": "Service configuration error.",
                "data": None,
                "errors": [str(exc)],
            },
        )
    if isinstance(exc, RetrievalEmbeddingError):
        logger.error("Retrieval embedding error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": "Embedding service is temporarily unavailable.",
                "data": None,
                "errors": [str(exc)],
            },
        )
    if isinstance(exc, RetrievalDatabaseError):
        logger.error("Retrieval database error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": "Vector database is temporarily unavailable.",
                "data": None,
                "errors": [str(exc)],
            },
        )
    # Catch-all — should not normally be reached; the global handler in
    # main.py will also catch it, but being explicit here aids debugging.
    logger.exception("Unexpected retrieval error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred during retrieval.",
            "data": None,
            "errors": [str(exc)],
        },
    )


# ---------------------------------------------------------------------------
# POST /retrieve  (primary endpoint)
# ---------------------------------------------------------------------------


@router.post(
    "/retrieve",
    summary="Semantic similarity search",
    description=(
        "Embed the query with Gemini `text-embedding-004`, search Qdrant using "
        "cosine similarity, and return the top-K most relevant text chunks.\n\n"
        "**Minimal request body:**\n"
        "```json\n"
        '{"query": "CPU Scheduling"}\n'
        "```\n\n"
        "**Status codes**\n"
        "- `200` — one or more matching chunks returned\n"
        "- `404` — query valid but no chunks found in the index\n"
        "- `422` — request body validation failed\n"
        "- `503` — Gemini or Qdrant is unreachable / misconfigured\n"
    ),
    response_model=SimpleRetrieveResponse,
    responses={
        200: {"description": "Matching chunks returned"},
        404: {"description": "No matching chunks found for this query"},
        422: {"description": "Request body validation failed"},
        503: {"description": "Embedding service or vector database unavailable"},
    },
    status_code=status.HTTP_200_OK,
)
async def retrieve(
    payload: SimpleRetrieveSchema,
    retrieval: RetrievalService = Depends(get_retrieval_service),
) -> SimpleRetrieveResponse | JSONResponse:
    """
    Run the end-to-end semantic retrieval pipeline.

    Pipeline
    ────────
    1. Validate request body (Pydantic / FastAPI — automatic 422 on failure).
    2. Generate a Gemini ``retrieval_query`` embedding for ``payload.query``.
    3. Run a cosine similarity search against the ``study_notes`` Qdrant collection.
    4. Return ranked :class:`SimpleRetrieveResult` objects.
    5. Return **404** when the index exists but the query matched nothing.

    The response shape always matches::

        {
            "query": "CPU Scheduling",
            "results": [
                {"score": 0.92, "text": "..."},
                ...
            ]
        }
    """
    logger.info(
        "POST /retrieve | query=%r | top_k=%d | threshold=%s | doc_id=%s",
        payload.query[:80],
        payload.top_k,
        payload.score_threshold,
        payload.document_id,
    )

    # ── Run the pipeline ────────────────────────────────────────────────
    try:
        results = retrieval.retrieve(
            query=payload.query,
            top_k=payload.top_k,
            score_threshold=payload.score_threshold,
            document_id=payload.document_id,
        )
    except (RetrievalConfigError, RetrievalEmbeddingError, RetrievalDatabaseError) as exc:
        return _handle_retrieval_error(exc)
    except Exception as exc:
        return _handle_retrieval_error(exc)

    # ── No results ──────────────────────────────────────────────────────
    if not results:
        logger.info("POST /retrieve | no results for query=%r", payload.query[:80])
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No matching chunks found for query: '{payload.query}'. "
                "Make sure documents have been uploaded and indexed."
            ),
        )

    # ── Success ─────────────────────────────────────────────────────────
    logger.info(
        "POST /retrieve | returning %d result(s) for query=%r",
        len(results),
        payload.query[:80],
    )
    return SimpleRetrieveResponse(query=payload.query, results=results)


# ---------------------------------------------------------------------------
# POST /retrieval/search  (full-featured search — existing endpoint)
# ---------------------------------------------------------------------------


@router.post(
    "/retrieval/search",
    summary="Full semantic search with filters",
    description=(
        "Extended search that supports document-ID and subject filters. "
        "Returns full :class:`ChunkResult` objects including page numbers and chunk index."
    ),
    response_model=APIResponse[RetrievalResponse],
    status_code=status.HTTP_200_OK,
)
async def semantic_search(
    payload: RetrievalQuerySchema,
    retrieval: RetrievalService = Depends(get_retrieval_service),
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[RetrievalResponse] | JSONResponse:
    """
    Perform a filtered semantic similarity search.

    - Embeds the query using Gemini.
    - Searches Qdrant with optional document-ID / subject filters.
    - Returns ranked :class:`ChunkResult` objects with full metadata.
    """
    logger.info(
        "POST /retrieval/search | query=%r | top_k=%s | doc_ids=%s",
        payload.query[:80],
        payload.top_k,
        payload.document_ids,
    )

    try:
        results = retrieval.search(
            query=payload.query,
            top_k=payload.top_k,
            score_threshold=payload.score_threshold,
            document_ids=payload.document_ids,
            subject=payload.subject,
        )
    except (RetrievalConfigError, RetrievalEmbeddingError, RetrievalDatabaseError) as exc:
        return _handle_retrieval_error(exc)
    except Exception as exc:
        return _handle_retrieval_error(exc)

    return APIResponse(
        success=True,
        message=f"Found {len(results)} result(s).",
        data=RetrievalResponse(
            query=payload.query,
            results=results,
            total_results=len(results),
        ),
    )


# ---------------------------------------------------------------------------
# POST /retrieval/ask  (RAG Q&A — existing endpoint)
# ---------------------------------------------------------------------------


@router.post(
    "/retrieval/ask",
    summary="RAG question answering",
    description=(
        "Retrieve relevant context from the vector index then use an LLM "
        "to generate a grounded answer. LLM generation is a future TODO; "
        "context retrieval is fully wired."
    ),
    response_model=APIResponse[AnswerResponse],
    status_code=status.HTTP_200_OK,
    responses={
        422: {"description": "Invalid request payload"},
        503: {"description": "Retrieval service unavailable"},
    },
)
async def ask_question(
    payload: AskQuestionSchema,
    retrieval: RetrievalService = Depends(get_retrieval_service),
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[AnswerResponse] | JSONResponse:
    """
    Answer a natural-language question using Retrieval-Augmented Generation.

    Current pipeline:
      1. Embed the question and retrieve top-K context chunks  ← **implemented**
      2. Build a prompt from the chunks and call the LLM       ← TODO
      3. Return the answer with source citations               ← TODO (placeholder)
    """
    logger.info(
        "POST /retrieval/ask | question=%r | doc_ids=%s | language=%s",
        payload.question[:80],
        payload.document_ids,
        payload.language,
    )

    try:
        context_chunks = retrieval.search(
            query=payload.question,
            top_k=payload.top_k,
            document_ids=payload.document_ids,
        )
    except (RetrievalConfigError, RetrievalEmbeddingError, RetrievalDatabaseError) as exc:
        return _handle_retrieval_error(exc)
    except Exception as exc:
        return _handle_retrieval_error(exc)

    # TODO: build prompt from context_chunks → call LLMService → parse response
    placeholder_answer = (
        "Answer generation is not yet implemented. "
        f"{len(context_chunks)} context chunk(s) were retrieved."
    )

    return APIResponse(
        success=True,
        message="Question processed.",
        data=AnswerResponse(
            question=payload.question,
            answer=placeholder_answer,
            source_chunks=context_chunks,
            model_used=settings.OPENAI_MODEL if settings else "unknown",
            tokens_used=None,
        ),
    )

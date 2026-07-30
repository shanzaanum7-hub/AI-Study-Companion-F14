"""
Retrieval Router

Exposes semantic search and RAG-based question answering endpoints.

  POST /retrieval/search   – similarity search over indexed chunks
  POST /retrieval/ask      – RAG question answering
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.models.response_models import (
    AnswerResponse,
    APIResponse,
    RetrievalResponse,
)
from app.models.schemas import AskQuestionSchema, RetrievalQuerySchema
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def get_retrieval_service() -> RetrievalService:
    """Provide a RetrievalService instance per request."""
    return RetrievalService()


def get_settings_dep() -> Settings:
    return get_settings()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/search",
    summary="Semantic similarity search",
    description=(
        "Embed the query and retrieve the top-K most relevant text chunks "
        "from the Qdrant vector index."
    ),
    response_model=APIResponse[RetrievalResponse],
    status_code=status.HTTP_200_OK,
)
async def semantic_search(
    payload: RetrievalQuerySchema,
    retrieval: RetrievalService = Depends(get_retrieval_service),
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[RetrievalResponse]:
    """
    Perform a semantic similarity search against all indexed documents.

    - Embeds the query using the configured embedding model.
    - Searches Qdrant for the nearest vectors.
    - Returns ranked text chunks with similarity scores.
    """
    logger.info(
        "Semantic search: query=%r, top_k=%s, doc_ids=%s",
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
    except Exception as exc:
        logger.exception("Semantic search failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed. Please try again later.",
        ) from exc

    return APIResponse(
        success=True,
        message=f"Found {len(results)} result(s).",
        data=RetrievalResponse(
            query=payload.query,
            results=results,
            total_results=len(results),
        ),
    )


@router.post(
    "/ask",
    summary="RAG question answering",
    description=(
        "Retrieve relevant context from the vector index and use an LLM "
        "to generate a grounded answer to the question."
    ),
    response_model=APIResponse[AnswerResponse],
    status_code=status.HTTP_200_OK,
    responses={
        422: {"description": "Invalid request payload"},
        500: {"description": "Retrieval or LLM error"},
    },
)
async def ask_question(
    payload: AskQuestionSchema,
    retrieval: RetrievalService = Depends(get_retrieval_service),
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[AnswerResponse]:
    """
    Answer a natural-language question using Retrieval-Augmented Generation.

    Pipeline (to be fully implemented in the service layer):
      1. Embed the question.
      2. Retrieve top-K context chunks from Qdrant.
      3. Build a prompt with the retrieved context.
      4. Send the prompt to the configured LLM.
      5. Return the answer alongside source chunks.
    """
    logger.info(
        "RAG ask: question=%r, doc_ids=%s, language=%s",
        payload.question[:80],
        payload.document_ids,
        payload.language,
    )

    # Step 1 & 2 — retrieve context chunks
    try:
        context_chunks = retrieval.search(
            query=payload.question,
            top_k=payload.top_k,
            document_ids=payload.document_ids,
        )
    except Exception as exc:
        logger.exception("Context retrieval failed for ask: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context. Please try again later.",
        ) from exc

    # Steps 3-5 are delegated to the LLM service (business logic placeholder)
    # TODO: build prompt from context_chunks, call LLMService, parse response

    # Placeholder response returned until LLM integration is complete
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

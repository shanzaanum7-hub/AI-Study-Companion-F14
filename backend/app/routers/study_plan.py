"""
Study Plan Router

Endpoints
─────────
POST /api/study-plan              Simple RAG study-plan generation  ← primary new endpoint
POST /api/v1/study-plan/generate  Full study-plan (existing, preserved)
POST /api/v1/study-plan/summary   Document summarisation (existing, preserved)
POST /api/v1/study-plan/flashcards  Flashcard generation (existing, preserved)

HTTP status codes
─────────────────
200  Study plan generated and validated successfully
404  No relevant context found in the index for the query
422  Request body failed Pydantic validation  (FastAPI automatic)
500  Unexpected / unclassified server error
503  Gemini unreachable, Qdrant unreachable, or API key missing
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.models.response_models import (
    APIResponse,
    Flashcard,
    FlashcardsResponse,
    SimpleStudyPlanResponse,
    StudyPlanResponse,
    SummaryResponse,
)
from app.models.schemas import (
    DifficultyLevel,
    GenerateFlashcardsSchema,
    GenerateStudyPlanSchema,
    GenerateSummarySchema,
    StudyPlanQuerySchema,
)
from app.services.study_plan_service import (
    StudyPlanEmptyContextError,
    StudyPlanJSONError,
    StudyPlanLLMError,
    StudyPlanRetrievalError,
    StudyPlanService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Study Plan"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def get_study_plan_service() -> StudyPlanService:
    """Provide a per-request StudyPlanService instance."""
    return StudyPlanService()


def get_settings_dep() -> Settings:
    return get_settings()


# ---------------------------------------------------------------------------
# Shared error-mapping helper
# ---------------------------------------------------------------------------


def _handle_study_plan_error(exc: Exception) -> JSONResponse:
    """
    Map domain-level StudyPlanError subtypes to the correct HTTP status
    and a consistent JSON body.

    Error → HTTP mapping
    ────────────────────
    StudyPlanEmptyContextError  → 404  (no indexed material for this topic)
    StudyPlanRetrievalError     → 503  (Qdrant / embedding service down)
    StudyPlanLLMError           → 503  (Gemini API unreachable)
    StudyPlanJSONError          → 500  (LLM produced unparseable output)
    Everything else             → 500  (unexpected)
    """
    if isinstance(exc, StudyPlanEmptyContextError):
        # Handled as HTTPException in the endpoint itself (raises 404)
        # This branch is a safety net if called directly.
        logger.warning("StudyPlanEmptyContextError: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": "No relevant study material found.",
                "data": None,
                "errors": [str(exc)],
            },
        )

    if isinstance(exc, StudyPlanRetrievalError):
        logger.error("StudyPlanRetrievalError: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": "Retrieval service is temporarily unavailable.",
                "data": None,
                "errors": [str(exc)],
            },
        )

    if isinstance(exc, StudyPlanLLMError):
        logger.error("StudyPlanLLMError: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": "LLM service is temporarily unavailable.",
                "data": None,
                "errors": [str(exc)],
            },
        )

    if isinstance(exc, StudyPlanJSONError):
        logger.error(
            "StudyPlanJSONError: %s | raw_response_preview=%r",
            exc,
            getattr(exc, "raw_response", "")[:200],
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "LLM returned an invalid response after all retry attempts.",
                "data": None,
                "errors": [str(exc)],
            },
        )

    # Catch-all
    logger.exception("Unexpected study-plan error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred while generating the study plan.",
            "data": None,
            "errors": [str(exc)],
        },
    )


# ---------------------------------------------------------------------------
# POST /study-plan  (primary endpoint)
# ---------------------------------------------------------------------------


@router.post(
    "/study-plan",
    summary="Generate a study plan",
    description=(
        "Run the full RAG pipeline to generate a structured study plan:\n\n"
        "1. Embed the query with Gemini `text-embedding-004`\n"
        "2. Retrieve top-K relevant chunks from Qdrant\n"
        "3. Build a grounded prompt from the retrieved material\n"
        "4. Call `gemini-1.5-flash` to generate a JSON study plan\n"
        "5. Validate the JSON — retry with a correction prompt if invalid\n\n"
        "**Minimal request body:**\n"
        "```json\n"
        '{"query": "CPU Scheduling"}\n'
        "```\n\n"
        "**Status codes**\n"
        "- `200` — valid study plan returned\n"
        "- `404` — no relevant documents found in the index\n"
        "- `422` — request body validation failed\n"
        "- `503` — Gemini or Qdrant is unreachable / misconfigured\n"
        "- `500` — LLM returned unparseable JSON after all retries\n"
    ),
    response_model=SimpleStudyPlanResponse,
    responses={
        200: {"description": "Study plan generated and validated successfully"},
        404: {"description": "No relevant study material found for this query"},
        422: {"description": "Request body validation failed"},
        503: {"description": "Gemini or Qdrant service unavailable"},
        500: {"description": "LLM returned invalid JSON after all retries"},
    },
    status_code=status.HTTP_200_OK,
)
async def generate_study_plan_simple(
    payload: StudyPlanQuerySchema,
    service: StudyPlanService = Depends(get_study_plan_service),
) -> SimpleStudyPlanResponse | JSONResponse:
    """
    Generate a structured study plan grounded in uploaded study material.

    The response always matches this exact shape::

        {
            "query": "CPU Scheduling",
            "model_used": "gemini-1.5-flash",
            "chunks_used": 5,
            "tokens_used": 1240,
            "plan": {
                "topic": "CPU Scheduling",
                "estimated_days": 5,
                "study_plan": [
                    {
                        "day": 1,
                        "focus": "Introduction to CPU Scheduling",
                        "tasks": [
                            "Read the retrieved material on scheduling algorithms",
                            "Summarise the difference between preemptive and non-preemptive scheduling"
                        ]
                    }
                ]
            }
        }
    """
    logger.info(
        "POST /study-plan | query=%r | top_k=%d | days=%d | difficulty=%s",
        payload.query[:80],
        payload.top_k,
        payload.duration_days,
        payload.difficulty.value,
    )

    # ── Run the full RAG → LLM → validate pipeline ──────────────────────
    try:
        result = service.generate(
            query=payload.query,
            top_k=payload.top_k,
            duration_days=payload.duration_days,
            difficulty=payload.difficulty,
        )

    # ── No context in the index ──────────────────────────────────────────
    except StudyPlanEmptyContextError as exc:
        logger.info("POST /study-plan | no context | query=%r", payload.query[:80])
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    # ── Service / infrastructure errors → mapped JSON responses ──────────
    except (StudyPlanRetrievalError, StudyPlanLLMError, StudyPlanJSONError) as exc:
        return _handle_study_plan_error(exc)

    # ── Unexpected errors ────────────────────────────────────────────────
    except Exception as exc:
        return _handle_study_plan_error(exc)

    # ── Success ──────────────────────────────────────────────────────────
    logger.info(
        "POST /study-plan | success | topic=%r | days=%d | chunks=%d | tokens=%s",
        result.plan.topic,
        result.plan.estimated_days,
        result.chunks_used,
        result.tokens_used,
    )
    return result


# ---------------------------------------------------------------------------
# POST /study-plan/generate  (existing verbose endpoint — preserved)
# ---------------------------------------------------------------------------


@router.post(
    "/study-plan/generate",
    summary="Generate a study plan (full options)",
    description=(
        "Full study-plan endpoint with difficulty, duration, language, and "
        "goal options. Uses the same RAG + Gemini pipeline as POST /study-plan "
        "but accepts the richer :class:`GenerateStudyPlanSchema` payload."
    ),
    response_model=APIResponse[StudyPlanResponse],
    status_code=status.HTTP_200_OK,
)
async def generate_study_plan_full(
    payload: GenerateStudyPlanSchema,
    service: StudyPlanService = Depends(get_study_plan_service),
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[StudyPlanResponse] | JSONResponse:
    """
    Generate a study plan using the full GenerateStudyPlanSchema.

    Delegates to :class:`StudyPlanService` using the same pipeline.
    Maps ``GenerateStudyPlanSchema`` → the simpler ``generate()`` arguments,
    then wraps the result in the legacy :class:`StudyPlanResponse` envelope
    for backward compatibility with existing clients.
    """
    logger.info(
        "POST /study-plan/generate | topic=%r | difficulty=%s | days=%d",
        payload.topic[:80],
        payload.difficulty.value,
        payload.duration_days,
    )

    try:
        simple_result = service.generate(
            query=payload.topic,
            top_k=5,
            duration_days=payload.duration_days,
            difficulty=payload.difficulty,
        )

    except StudyPlanEmptyContextError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except (StudyPlanRetrievalError, StudyPlanLLMError, StudyPlanJSONError) as exc:
        return _handle_study_plan_error(exc)
    except Exception as exc:
        return _handle_study_plan_error(exc)

    # Wrap the validated plan into the legacy StudyPlanResponse envelope
    legacy_response = StudyPlanResponse(
        plan_id=uuid.uuid4(),
        topic=simple_result.plan.topic,
        difficulty=payload.difficulty.value,
        duration_days=simple_result.plan.estimated_days,
        daily_study_minutes=payload.daily_study_minutes,
        language=payload.language.value,
        overview=(
            f"AI-generated study plan for '{simple_result.plan.topic}' "
            f"based on {simple_result.chunks_used} retrieved chunk(s)."
        ),
        learning_objectives=[
            day.focus for day in simple_result.plan.study_plan
        ],
        schedule=[],
        created_at=datetime.now(timezone.utc),
    )

    return APIResponse(
        success=True,
        message="Study plan generated successfully.",
        data=legacy_response,
    )


# ---------------------------------------------------------------------------
# POST /study-plan/summary  (existing — preserved)
# ---------------------------------------------------------------------------


@router.post(
    "/study-plan/summary",
    summary="Summarise a topic or documents",
    description=(
        "Generate a concise summary of one or more uploaded documents, "
        "optionally focused on a specific topic."
    ),
    response_model=APIResponse[SummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def generate_summary(
    payload: GenerateSummarySchema,
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[SummaryResponse]:
    """
    Summarise documents or a topic using RAG + LLM.

    TODO: wire up LLM summarisation logic (same pattern as study-plan).
    """
    if not payload.document_ids and not payload.topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of: document_ids, topic.",
        )

    logger.info(
        "POST /study-plan/summary | topic=%r | doc_ids=%s",
        payload.topic,
        payload.document_ids,
    )

    # TODO: retrieve context → call LLMService → return real summary
    return APIResponse(
        success=True,
        message="Summary generated successfully.",
        data=SummaryResponse(
            topic=payload.topic,
            summary=(
                f"Placeholder summary for topic='{payload.topic}'. "
                "LLM summarisation is not yet implemented."
            ),
            word_count=0,
            language=payload.language.value,
            source_document_ids=payload.document_ids or [],
            created_at=datetime.now(timezone.utc),
        ),
    )


# ---------------------------------------------------------------------------
# POST /study-plan/flashcards  (existing — preserved)
# ---------------------------------------------------------------------------


@router.post(
    "/study-plan/flashcards",
    summary="Generate flashcards",
    description=(
        "Create a set of question-and-answer flashcards from uploaded "
        "documents or a specified topic."
    ),
    response_model=APIResponse[FlashcardsResponse],
    status_code=status.HTTP_200_OK,
)
async def generate_flashcards(
    payload: GenerateFlashcardsSchema,
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[FlashcardsResponse]:
    """
    Generate flashcards using RAG + LLM.

    TODO: wire up LLM flashcard logic (same pattern as study-plan).
    """
    if not payload.document_ids and not payload.topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of: document_ids, topic.",
        )

    logger.info(
        "POST /study-plan/flashcards | topic=%r | num_cards=%d",
        payload.topic,
        payload.num_cards,
    )

    # TODO: retrieve context → call LLMService → parse Q&A pairs
    placeholder_cards = [
        Flashcard(
            card_id=i,
            question=f"[Placeholder] Question {i} about '{payload.topic}'",
            answer=f"[Placeholder] Answer {i}",
            hint=None,
            difficulty=payload.difficulty.value,
        )
        for i in range(1, min(payload.num_cards + 1, 4))
    ]

    return APIResponse(
        success=True,
        message=f"Generated {len(placeholder_cards)} flashcard(s).",
        data=FlashcardsResponse(
            topic=payload.topic,
            language=payload.language.value,
            total_cards=len(placeholder_cards),
            cards=placeholder_cards,
            created_at=datetime.now(timezone.utc),
        ),
    )

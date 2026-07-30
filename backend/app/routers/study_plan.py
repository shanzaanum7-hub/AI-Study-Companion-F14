"""
Study Plan Router

AI-powered study assistance endpoints:
  POST /study-plan/generate    – generate a personalised study plan
  POST /study-plan/summary     – summarise documents or a topic
  POST /study-plan/flashcards  – generate flashcards from documents or a topic
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.models.response_models import (
    APIResponse,
    Flashcard,
    FlashcardsResponse,
    StudyPlanResponse,
    SummaryResponse,
)
from app.models.schemas import (
    GenerateFlashcardsSchema,
    GenerateStudyPlanSchema,
    GenerateSummarySchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study-plan", tags=["Study Plan"])


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def get_settings_dep() -> Settings:
    return get_settings()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/generate",
    summary="Generate a study plan",
    description=(
        "Use an LLM to produce a structured, day-by-day study schedule "
        "tailored to the provided topic, difficulty, and duration."
    ),
    response_model=APIResponse[StudyPlanResponse],
    status_code=status.HTTP_200_OK,
)
async def generate_study_plan(
    payload: GenerateStudyPlanSchema,
    settings: Annotated[Settings, Depends(get_settings_dep)] = None,
) -> APIResponse[StudyPlanResponse]:
    """
    Generate a personalised study plan.

    Full implementation will:
      1. Retrieve relevant chunks for *payload.topic* from Qdrant.
      2. Build a structured prompt.
      3. Call the LLM service.
      4. Parse the response into a :class:`StudyPlanResponse`.

    Currently returns a well-shaped placeholder so the API contract is
    testable end-to-end before business logic is added.
    """
    logger.info(
        "Generate study plan: topic=%r, difficulty=%s, days=%d",
        payload.topic,
        payload.difficulty.value,
        payload.duration_days,
    )

    # TODO: retrieve context, call LLMService, parse structured response

    placeholder = StudyPlanResponse(
        plan_id=uuid.uuid4(),
        topic=payload.topic,
        difficulty=payload.difficulty.value,
        duration_days=payload.duration_days,
        daily_study_minutes=payload.daily_study_minutes,
        language=payload.language.value,
        overview=(
            f"Placeholder study plan for '{payload.topic}'. "
            "LLM integration is not yet implemented."
        ),
        learning_objectives=[
            f"Understand the fundamentals of {payload.topic}",
            "Apply key concepts through practice",
            "Review and consolidate knowledge",
        ],
        schedule=[],
        created_at=datetime.now(timezone.utc),
    )

    return APIResponse(
        success=True,
        message="Study plan generated successfully.",
        data=placeholder,
    )


@router.post(
    "/summary",
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

    Full implementation will:
      1. Retrieve relevant context from Qdrant.
      2. Build a summarisation prompt.
      3. Call the LLM and return the result.
    """
    if not payload.document_ids and not payload.topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of: document_ids, topic.",
        )

    logger.info(
        "Generate summary: topic=%r, doc_ids=%s, max_words=%d",
        payload.topic,
        payload.document_ids,
        payload.max_words,
    )

    # TODO: retrieve context, call LLMService, return real summary

    placeholder = SummaryResponse(
        topic=payload.topic,
        summary=(
            f"Placeholder summary for topic='{payload.topic}'. "
            "LLM integration is not yet implemented."
        ),
        word_count=0,
        language=payload.language.value,
        source_document_ids=payload.document_ids or [],
        created_at=datetime.now(timezone.utc),
    )

    return APIResponse(
        success=True,
        message="Summary generated successfully.",
        data=placeholder,
    )


@router.post(
    "/flashcards",
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

    Full implementation will:
      1. Retrieve relevant context chunks.
      2. Prompt the LLM to produce Q&A pairs.
      3. Parse and return a :class:`FlashcardsResponse`.
    """
    if not payload.document_ids and not payload.topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of: document_ids, topic.",
        )

    logger.info(
        "Generate flashcards: topic=%r, num_cards=%d, difficulty=%s",
        payload.topic,
        payload.num_cards,
        payload.difficulty.value,
    )

    # TODO: retrieve context, call LLMService, parse flashcard pairs

    placeholder_cards = [
        Flashcard(
            card_id=i,
            question=f"[Placeholder] Question {i} about '{payload.topic}'",
            answer=f"[Placeholder] Answer {i}",
            hint=None,
            difficulty=payload.difficulty.value,
        )
        for i in range(1, min(payload.num_cards + 1, 4))  # return 3 placeholder cards
    ]

    response = FlashcardsResponse(
        topic=payload.topic,
        language=payload.language.value,
        total_cards=len(placeholder_cards),
        cards=placeholder_cards,
        created_at=datetime.now(timezone.utc),
    )

    return APIResponse(
        success=True,
        message=f"Generated {len(placeholder_cards)} flashcard(s).",
        data=response,
    )

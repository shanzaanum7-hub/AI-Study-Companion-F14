"""
Pydantic request/payload schemas.

These models validate incoming data at the API boundary.
No business logic lives here — only shape + constraint definitions.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared / primitive types
# ---------------------------------------------------------------------------


class LanguageCode(str, Enum):
    """ISO 639-1 language codes supported by the study companion."""

    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    ZH = "zh"
    AR = "ar"


class DifficultyLevel(str, Enum):
    """Difficulty levels used across study-plan and quiz generation."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ---------------------------------------------------------------------------
# Upload schemas
# ---------------------------------------------------------------------------


class UploadMetadataSchema(BaseModel):
    """Optional metadata that the client may send alongside a file upload."""

    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable document title (defaults to filename)",
    )
    subject: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Subject or topic the document belongs to",
    )
    language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Primary language of the document",
    )
    tags: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Free-form tags for filtering (max 10)",
    )

    @field_validator("tags")
    @classmethod
    def normalise_tags(cls, value: List[str]) -> List[str]:
        """Strip whitespace and lower-case every tag."""
        return [tag.strip().lower() for tag in value if tag.strip()]


# ---------------------------------------------------------------------------
# Retrieval schemas
# ---------------------------------------------------------------------------


class SimpleRetrieveSchema(BaseModel):
    """
    Minimal payload for the POST /api/retrieve endpoint.

    Only ``query`` is required. Optional fields allow callers to narrow
    the search scope or tune result quality without extra endpoints.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural-language question or keyword to search for",
        examples=["CPU Scheduling"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of chunks to return (default: 5)",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score (0–1). Omit to return all top-k results.",
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Restrict search to a single document by its ID",
    )


class RetrievalQuerySchema(BaseModel):
    """Payload for a semantic similarity search."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural-language question or keyword query",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Override the default number of results to return",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Override the minimum similarity score",
    )
    document_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Restrict search to a specific set of document IDs",
    )
    subject: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filter by subject tag",
    )


class AskQuestionSchema(BaseModel):
    """Payload for RAG-based question answering."""

    question: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="The question to answer using retrieved context",
    )
    document_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Limit context retrieval to these document IDs",
    )
    language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Language in which the answer should be generated",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of chunks to retrieve as context",
    )


# ---------------------------------------------------------------------------
# Study-plan schemas
# ---------------------------------------------------------------------------


class StudyPlanQuerySchema(BaseModel):
    """
    Minimal payload for the POST /api/study-plan endpoint.

    Mirrors the same lean design as :class:`SimpleRetrieveSchema` —
    only ``query`` is required.  The service layer derives everything else
    (retrieval top-k, prompt language, day count) from application defaults
    so the client stays simple.

    Example request body::

        {"query": "CPU Scheduling"}
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Topic or question to generate a study plan for",
        examples=["CPU Scheduling"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of context chunks to retrieve from the index (default: 5)",
    )
    duration_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Desired plan length in days (default: 7)",
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE,
        description="Target difficulty level",
    )


class GenerateStudyPlanSchema(BaseModel):
    """Payload for AI-generated study plan creation."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="The topic or subject the student wants to study",
    )
    document_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Source documents to base the study plan on",
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE,
        description="Target difficulty level for the generated plan",
    )
    duration_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Total number of days the plan should span",
    )
    daily_study_minutes: int = Field(
        default=60,
        ge=15,
        le=480,
        description="Target study minutes per day",
    )
    language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Language in which the plan should be generated",
    )
    goals: Optional[List[str]] = Field(
        default=None,
        max_length=10,
        description="Specific learning goals (max 10)",
    )


class GenerateSummarySchema(BaseModel):
    """Payload for document or topic summarisation."""

    document_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Documents to summarise (omit to summarise by topic)",
    )
    topic: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Narrow the summary to a specific topic within the documents",
    )
    max_words: int = Field(
        default=300,
        ge=50,
        le=2000,
        description="Approximate maximum word count for the summary",
    )
    language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Output language for the summary",
    )


class GenerateFlashcardsSchema(BaseModel):
    """Payload for AI-generated flashcard creation."""

    document_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Source documents (omit to derive from topic)",
    )
    topic: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Topic to generate flashcards for",
    )
    num_cards: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of flashcards to generate",
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE,
        description="Target difficulty for the flashcards",
    )
    language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Language for the generated flashcards",
    )

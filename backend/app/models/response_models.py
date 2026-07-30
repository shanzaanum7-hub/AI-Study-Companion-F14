"""
Standardised API response models.

Every endpoint returns one of these envelopes so that clients always receive
a predictable JSON structure regardless of the operation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel  # Pydantic v1 compat shim kept for clarity

# ---------------------------------------------------------------------------
# Generic envelope
# ---------------------------------------------------------------------------

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """
    Top-level envelope for every API response.

    Attributes:
        success:    Whether the operation completed without errors.
        message:    Human-readable summary of the outcome.
        data:       Typed payload; None on error responses.
        errors:     List of error detail strings (populated on failure).
        timestamp:  UTC timestamp of when the response was generated.
    """

    success: bool = Field(..., description="True if the request succeeded")
    message: str = Field(..., description="Human-readable result summary")
    data: Optional[DataT] = Field(default=None, description="Response payload")
    errors: Optional[List[str]] = Field(default=None, description="Error details when success=False")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the response",
    )

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationMeta(BaseModel):
    """Metadata included in paginated list responses."""

    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_items: int = Field(..., ge=0, description="Total items across all pages")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Envelope for paginated list endpoints."""

    success: bool = True
    message: str = "OK"
    data: List[DataT] = Field(default_factory=list)
    pagination: PaginationMeta
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Document / Upload response models
# ---------------------------------------------------------------------------


class DocumentResponse(BaseModel):
    """Represents a successfully uploaded and processed document."""

    document_id: UUID = Field(..., description="Unique identifier for the document")
    filename: str = Field(..., description="Original filename of the uploaded file")
    title: Optional[str] = Field(default=None, description="Human-readable title")
    subject: Optional[str] = Field(default=None, description="Subject or topic")
    language: str = Field(..., description="Primary language of the document")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    num_chunks: int = Field(..., ge=0, description="Number of text chunks indexed")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    status: str = Field(..., description="Processing status: pending | processing | ready | failed")
    created_at: datetime = Field(..., description="UTC timestamp of upload")


class UploadResponse(BaseModel):
    """Immediate response returned after a file upload is accepted."""

    document_id: UUID = Field(..., description="Assigned document identifier")
    filename: str = Field(..., description="Stored filename")
    status: str = Field(..., description="Initial processing status")
    message: str = Field(..., description="Status message")


# ---------------------------------------------------------------------------
# Retrieval response models
# ---------------------------------------------------------------------------


class ChunkResult(BaseModel):
    """A single retrieved text chunk with relevance metadata."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: UUID = Field(..., description="Parent document ID")
    document_title: Optional[str] = Field(default=None, description="Title of the source document")
    text: str = Field(..., description="The raw text content of the chunk")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (higher is more relevant)")
    page_number: Optional[int] = Field(default=None, description="Page number in the source PDF")
    chunk_index: int = Field(..., ge=0, description="Zero-based index of the chunk within the document")


class RetrievalResponse(BaseModel):
    """Result of a semantic search query."""

    query: str = Field(..., description="The original search query")
    results: List[ChunkResult] = Field(default_factory=list, description="Ranked list of matching chunks")
    total_results: int = Field(..., ge=0, description="Number of chunks returned")


class AnswerResponse(BaseModel):
    """Result of a RAG-based question-answering request."""

    question: str = Field(..., description="The original question")
    answer: str = Field(..., description="AI-generated answer")
    source_chunks: List[ChunkResult] = Field(
        default_factory=list,
        description="Context chunks used to generate the answer",
    )
    model_used: str = Field(..., description="LLM model that produced the answer")
    tokens_used: Optional[int] = Field(default=None, description="Total tokens consumed (prompt + completion)")


# ---------------------------------------------------------------------------
# Study-plan response models
# ---------------------------------------------------------------------------


class StudySession(BaseModel):
    """A single study session within a day."""

    session_number: int = Field(..., ge=1, description="Session index within the day")
    topic: str = Field(..., description="Topic or concept to cover")
    description: str = Field(..., description="Brief description of the session content")
    duration_minutes: int = Field(..., ge=1, description="Recommended duration in minutes")
    resources: List[str] = Field(default_factory=list, description="Suggested resources or activities")


class StudyDay(BaseModel):
    """All study sessions scheduled for a given day."""

    day: int = Field(..., ge=1, description="Day number in the plan (1-indexed)")
    date: Optional[str] = Field(default=None, description="ISO date string (YYYY-MM-DD) if a start date was provided")
    sessions: List[StudySession] = Field(default_factory=list, description="Ordered sessions for the day")
    daily_goal: str = Field(..., description="Primary learning goal for the day")


class StudyPlanResponse(BaseModel):
    """An AI-generated structured study plan."""

    plan_id: UUID = Field(..., description="Unique plan identifier")
    topic: str = Field(..., description="Top-level study topic")
    difficulty: str = Field(..., description="Target difficulty level")
    duration_days: int = Field(..., ge=1, description="Total plan duration in days")
    daily_study_minutes: int = Field(..., ge=1, description="Target minutes per day")
    language: str = Field(..., description="Language of the plan content")
    overview: str = Field(..., description="High-level overview of the study plan")
    learning_objectives: List[str] = Field(default_factory=list, description="Key learning objectives")
    schedule: List[StudyDay] = Field(default_factory=list, description="Day-by-day schedule")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Flashcard(BaseModel):
    """A single question-and-answer flashcard."""

    card_id: int = Field(..., ge=1, description="Card index within the set")
    question: str = Field(..., description="Front of the card — the question or prompt")
    answer: str = Field(..., description="Back of the card — the answer or explanation")
    hint: Optional[str] = Field(default=None, description="Optional hint to aid recall")
    difficulty: str = Field(..., description="Difficulty level of this card")


class FlashcardsResponse(BaseModel):
    """A set of AI-generated flashcards."""

    topic: Optional[str] = Field(default=None, description="Topic the cards cover")
    language: str = Field(..., description="Language of the card content")
    total_cards: int = Field(..., ge=0, description="Number of cards in the set")
    cards: List[Flashcard] = Field(default_factory=list, description="The flashcard set")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SummaryResponse(BaseModel):
    """An AI-generated text summary."""

    topic: Optional[str] = Field(default=None, description="Topic the summary focuses on")
    summary: str = Field(..., description="The generated summary text")
    word_count: int = Field(..., ge=0, description="Approximate word count of the summary")
    language: str = Field(..., description="Language of the summary")
    source_document_ids: List[UUID] = Field(
        default_factory=list,
        description="IDs of documents used as source material",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Health response model
# ---------------------------------------------------------------------------


class ServiceStatus(BaseModel):
    """Status of a single dependent service."""

    name: str = Field(..., description="Service name")
    status: str = Field(..., description="ok | degraded | unavailable")
    latency_ms: Optional[float] = Field(default=None, description="Round-trip latency in milliseconds")
    detail: Optional[str] = Field(default=None, description="Additional status detail or error message")


class HealthResponse(BaseModel):
    """Aggregated health-check response."""

    status: str = Field(..., description="Overall status: healthy | degraded | unhealthy")
    version: str = Field(..., description="Application version string")
    environment: str = Field(..., description="Runtime environment name")
    uptime_seconds: float = Field(..., ge=0, description="Seconds since the application started")
    services: List[ServiceStatus] = Field(default_factory=list, description="Status of each downstream service")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

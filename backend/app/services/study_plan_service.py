"""
Study Plan Service

Implements the full RAG pipeline for POST /api/study-plan:

    user query
        │
        ▼  Step 1
    RetrievalService.retrieve()     ← embed query → search Qdrant → top-K chunks
        │
        ▼  Step 2
    _build_prompt()                 ← inject chunks into structured system prompt
        │
        ▼  Step 3
    GeminiProvider.chat()           ← call Gemini with retry (via LLMService)
        │
        ▼  Step 4
    _extract_json()                 ← strip markdown fences, isolate JSON object
        │
        ▼  Step 5
    _validate_plan()                ← Pydantic parse → StudyPlanResult
        │  ↑ ValidationError? retry from Step 3 with correction prompt
        ▼
    SimpleStudyPlanResponse         ← returned to router

Retry logic
───────────
  MAX_JSON_RETRIES (default 3) controls how many times the service will
  re-prompt Gemini when it returns malformed or structurally invalid JSON.
  Each retry sends the previous bad response back to Gemini with an explicit
  correction instruction so the model can self-correct.

Only this module knows about both the retrieval service and the LLM service.
The router imports only :class:`StudyPlanService` and the domain exceptions.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import List, Optional

from pydantic import ValidationError

from app.models.response_models import (
    SimpleStudyPlanResponse,
    StudyPlanDay,
    StudyPlanResult,
)
from app.models.schemas import DifficultyLevel
from app.services.llm_service import LLMService, Message
from app.services.retrieval_service import (
    RetrievalConfigError,
    RetrievalDatabaseError,
    RetrievalEmbeddingError,
    RetrievalService,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level configuration (read from env so no settings import is needed
# for these study-plan-specific knobs)
# ---------------------------------------------------------------------------

_GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
_MAX_JSON_RETRIES: int = int(os.getenv("STUDY_PLAN_MAX_JSON_RETRIES", 3))
_RETRY_BACKOFF: float = float(os.getenv("STUDY_PLAN_RETRY_BACKOFF", 1.5))


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class StudyPlanError(Exception):
    """Base class for all study-plan pipeline errors."""


class StudyPlanRetrievalError(StudyPlanError):
    """Raised when the context-retrieval step fails."""


class StudyPlanLLMError(StudyPlanError):
    """Raised when the Gemini call fails after all retries."""


class StudyPlanJSONError(StudyPlanError):
    """
    Raised when Gemini returns JSON that cannot be parsed or validated
    even after all self-correction retries.
    """

    def __init__(self, message: str, raw_response: str = "") -> None:
        super().__init__(message)
        self.raw_response = raw_response


class StudyPlanEmptyContextError(StudyPlanError):
    """Raised when no relevant chunks are found for the query."""


# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an AI Study Assistant.

Your ONLY job is to generate a structured study plan based EXCLUSIVELY on the
study material provided below.

Rules you MUST follow:
1. Never use external knowledge — only the retrieved study material.
2. Return ONLY a single valid JSON object. No markdown, no prose, no code fences.
3. The JSON must conform exactly to this schema:
   {
     "topic": "<string>",
     "estimated_days": <integer ≥ 1>,
     "study_plan": [
       {
         "day": <integer, 1-indexed>,
         "focus": "<string — main concept for this day>",
         "tasks": ["<string task>", ...]
       }
     ]
   }
4. "estimated_days" must equal the number of objects in "study_plan".
5. Every day must have at least two tasks.
6. Do not wrap the JSON in ```json``` fences or any other text.
"""

_CORRECTION_PROMPT_TEMPLATE = """\
Your previous response was not valid JSON or did not match the required schema.

Error: {error}

Your previous response was:
{bad_response}

Please respond ONLY with a corrected, valid JSON object matching this exact schema:
{{
  "topic": "<string>",
  "estimated_days": <integer>,
  "study_plan": [
    {{
      "day": <integer>,
      "focus": "<string>",
      "tasks": ["<string>", ...]
    }}
  ]
}}
No markdown. No explanations. JSON only.
"""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class StudyPlanService:
    """
    Orchestrates the full RAG → Gemini → JSON-validation pipeline.

    Args:
        retrieval_service: Injected :class:`RetrievalService` (default: new instance).
        llm_service:       Injected :class:`LLMService` (default: Gemini provider).
    """

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMService] = None,
    ) -> None:
        self._retrieval = retrieval_service or RetrievalService()
        self._llm = llm_service or LLMService(provider="gemini")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        query: str,
        top_k: int = 5,
        duration_days: int = 7,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
    ) -> SimpleStudyPlanResponse:
        """
        Run the full study-plan generation pipeline.

        Pipeline
        ────────
        1. Retrieve top-K context chunks from Qdrant.
        2. Raise :exc:`StudyPlanEmptyContextError` if the index returns nothing.
        3. Build a system prompt + user prompt containing the chunks.
        4. Call Gemini and request valid JSON.
        5. Extract the JSON object from the raw response.
        6. Validate the JSON against :class:`StudyPlanResult` with Pydantic.
        7. If validation fails, re-prompt Gemini (up to MAX_JSON_RETRIES times).
        8. Raise :exc:`StudyPlanJSONError` if all retries are exhausted.

        Args:
            query:         Natural-language study topic / question.
            top_k:         Number of context chunks to retrieve.
            duration_days: Desired plan length in days (passed as a hint to Gemini).
            difficulty:    Desired difficulty level (passed as a hint to Gemini).

        Returns:
            :class:`SimpleStudyPlanResponse` with the validated plan.

        Raises:
            StudyPlanEmptyContextError: No context chunks found.
            StudyPlanRetrievalError:    Retrieval pipeline failed.
            StudyPlanLLMError:          Gemini call failed after all retries.
            StudyPlanJSONError:         LLM output could not be parsed / validated.
        """
        query = query.strip()
        logger.info(
            "StudyPlanService.generate | query=%r | top_k=%d | days=%d | difficulty=%s",
            query[:80],
            top_k,
            duration_days,
            difficulty.value,
        )

        # ── Step 1: Retrieve context ─────────────────────────────────────
        chunks = self._retrieve_context(query, top_k)

        # ── Step 2: Guard — no context ───────────────────────────────────
        if not chunks:
            logger.warning(
                "No context chunks found for query=%r. Cannot generate study plan.", query
            )
            raise StudyPlanEmptyContextError(
                f"No relevant study material found for '{query}'. "
                "Please upload and index relevant documents first."
            )

        logger.info("Retrieved %d context chunk(s) for study plan generation.", len(chunks))

        # ── Step 3: Build prompts ────────────────────────────────────────
        system_msg, user_msg = self._build_prompt(
            query=query,
            chunks=chunks,
            duration_days=duration_days,
            difficulty=difficulty,
        )

        # ── Steps 4-7: Call LLM with JSON-validation retry loop ──────────
        plan, tokens_used = self._generate_with_retry(system_msg, user_msg)

        # ── Step 8: Build and return the response ────────────────────────
        response = SimpleStudyPlanResponse(
            query=query,
            model_used=_GEMINI_CHAT_MODEL,
            chunks_used=len(chunks),
            tokens_used=tokens_used,
            plan=plan,
        )

        logger.info(
            "Study plan generated | topic=%r | days=%d | chunks=%d | tokens=%s",
            plan.topic,
            plan.estimated_days,
            len(chunks),
            tokens_used,
        )
        return response

    # ------------------------------------------------------------------
    # Step 1 — Retrieval
    # ------------------------------------------------------------------

    def _retrieve_context(self, query: str, top_k: int) -> List[str]:
        """
        Retrieve the top-K most relevant text chunks for the query.

        Returns:
            List of plain text strings (chunk content only — no metadata).

        Raises:
            StudyPlanRetrievalError: If the retrieval pipeline raises any error.
        """
        try:
            results = self._retrieval.retrieve(query=query, top_k=top_k)
            return [r.text for r in results if r.text.strip()]
        except (RetrievalConfigError, RetrievalEmbeddingError, RetrievalDatabaseError) as exc:
            raise StudyPlanRetrievalError(
                f"Failed to retrieve context for study plan: {exc}"
            ) from exc
        except Exception as exc:
            raise StudyPlanRetrievalError(
                f"Unexpected retrieval error: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Step 2 — Prompt construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompt(
        query: str,
        chunks: List[str],
        duration_days: int,
        difficulty: DifficultyLevel,
    ) -> tuple[Message, Message]:
        """
        Construct the system and user :class:`Message` objects for Gemini.

        The system message carries the strict JSON-only instruction.
        The user message contains the retrieved context and the generation
        request, so Gemini always sees the material it must ground itself in.

        Args:
            query:        Original user query.
            chunks:       Retrieved text chunks (plain strings).
            duration_days: Hint for plan length.
            difficulty:   Hint for difficulty level.

        Returns:
            (system_message, user_message) tuple ready for LLMService.chat().
        """
        # Number the chunks so the model can reference them if needed
        context_block = "\n\n".join(
            f"[Chunk {i + 1}]\n{chunk.strip()}"
            for i, chunk in enumerate(chunks)
        )

        user_content = (
            f"STUDY MATERIAL:\n"
            f"{'─' * 60}\n"
            f"{context_block}\n"
            f"{'─' * 60}\n\n"
            f"REQUEST:\n"
            f"Topic: {query}\n"
            f"Target duration: {duration_days} day(s)\n"
            f"Difficulty: {difficulty.value}\n\n"
            f"Using ONLY the study material above, generate a structured study plan "
            f"in the required JSON format."
        )

        system_msg = Message(role="system", content=_SYSTEM_PROMPT)
        user_msg = Message(role="user", content=user_content)

        logger.debug(
            "Built prompt | chunks=%d | context_chars=%d",
            len(chunks),
            len(context_block),
        )
        return system_msg, user_msg

    # ------------------------------------------------------------------
    # Steps 3-7 — LLM call + JSON validation with retry
    # ------------------------------------------------------------------

    def _generate_with_retry(
        self,
        system_msg: Message,
        user_msg: Message,
    ) -> tuple[StudyPlanResult, Optional[int]]:
        """
        Call Gemini and validate the JSON response, retrying on failure.

        Retry strategy
        ──────────────
        - Attempt 1: send the original system + user prompt.
        - Attempt N (N > 1): send a correction prompt that includes the
          previous bad response and the specific validation error, giving
          Gemini a chance to self-correct without losing context.

        Args:
            system_msg: System :class:`Message` with the JSON contract.
            user_msg:   User :class:`Message` with context + request.

        Returns:
            (StudyPlanResult, tokens_used)

        Raises:
            StudyPlanLLMError:  Gemini call itself raised an exception.
            StudyPlanJSONError: All retries exhausted with invalid JSON.
        """
        last_raw: str = ""
        last_error: str = ""
        total_tokens: Optional[int] = None

        for attempt in range(1, _MAX_JSON_RETRIES + 1):
            logger.info(
                "Gemini call attempt %d/%d", attempt, _MAX_JSON_RETRIES
            )

            # Build messages list — use correction prompt from attempt 2 onward
            if attempt == 1:
                messages = [system_msg, user_msg]
            else:
                logger.warning(
                    "JSON validation failed (attempt %d). Sending correction prompt. Error: %s",
                    attempt - 1,
                    last_error,
                )
                correction_content = _CORRECTION_PROMPT_TEMPLATE.format(
                    error=last_error,
                    bad_response=last_raw[:2000],  # truncate to avoid token overflow
                )
                messages = [
                    system_msg,
                    user_msg,
                    Message(role="assistant", content=last_raw),
                    Message(role="user", content=correction_content),
                ]
                time.sleep(_RETRY_BACKOFF * (attempt - 1))

            # ── Call the LLM ─────────────────────────────────────────────
            try:
                llm_response = self._llm.chat(messages=messages)
            except Exception as exc:
                raise StudyPlanLLMError(
                    f"Gemini API call failed on attempt {attempt}: {exc}"
                ) from exc

            last_raw = llm_response.content.strip()
            total_tokens = llm_response.tokens_used

            logger.debug(
                "Gemini raw response (attempt %d) | chars=%d | tokens=%s",
                attempt,
                len(last_raw),
                total_tokens,
            )

            # ── Extract JSON ──────────────────────────────────────────────
            json_str, extract_error = self._extract_json(last_raw)
            if extract_error:
                last_error = extract_error
                logger.warning("JSON extraction failed (attempt %d): %s", attempt, extract_error)
                continue

            # ── Validate with Pydantic ────────────────────────────────────
            plan, validate_error = self._validate_plan(json_str)
            if validate_error:
                last_error = validate_error
                logger.warning("Pydantic validation failed (attempt %d): %s", attempt, validate_error)
                continue

            # ── Success ───────────────────────────────────────────────────
            logger.info(
                "Valid study plan received on attempt %d | topic=%r | days=%d",
                attempt,
                plan.topic,
                plan.estimated_days,
            )
            return plan, total_tokens

        # All retries exhausted
        raise StudyPlanJSONError(
            f"Gemini returned invalid JSON after {_MAX_JSON_RETRIES} attempt(s). "
            f"Last error: {last_error}",
            raw_response=last_raw,
        )

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(raw: str) -> tuple[str, str]:
        """
        Extract a JSON object string from a raw LLM response.

        Handles these common Gemini output patterns:
          1. Pure JSON object (ideal case).
          2. JSON wrapped in ```json ... ``` code fences.
          3. JSON wrapped in ``` ... ``` code fences (no language tag).
          4. JSON object embedded in surrounding prose — locate by
             finding the first ``{`` and last ``}``.

        Args:
            raw: Raw text content from the Gemini response.

        Returns:
            (json_string, error_string)
            If extraction succeeded: (json_str, "")
            If it failed:            ("", error_description)
        """
        if not raw:
            return "", "LLM returned an empty response."

        # Pattern 1: strip ```json ... ``` or ``` ... ``` fences
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1).strip()
            if candidate.startswith("{"):
                return candidate, ""

        # Pattern 2: find outermost { ... } — handles prose wrapping
        first_brace = raw.find("{")
        last_brace = raw.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            candidate = raw[first_brace : last_brace + 1]
            return candidate, ""

        return "", (
            "Could not locate a JSON object in the response. "
            f"Response starts with: {raw[:200]!r}"
        )

    # ------------------------------------------------------------------
    # JSON validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_plan(json_str: str) -> tuple[Optional[StudyPlanResult], str]:
        """
        Parse a JSON string and validate it against :class:`StudyPlanResult`.

        Validation checks performed by Pydantic:
          - ``topic``          is a non-empty string.
          - ``estimated_days`` is an integer ≥ 1.
          - ``study_plan``     is a non-empty list of :class:`StudyPlanDay`.
          - Each day has ``day`` (int ≥ 1), ``focus`` (str), ``tasks`` (list).

        Args:
            json_str: Candidate JSON string.

        Returns:
            (StudyPlanResult, "") on success.
            (None, error_description) on failure.
        """
        # Step 1 — parse raw JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            return None, f"JSON decode error at position {exc.pos}: {exc.msg}"

        if not isinstance(data, dict):
            return None, (
                f"Expected a JSON object (dict) at the top level, "
                f"got {type(data).__name__}."
            )

        # Step 2 — Pydantic structural validation
        try:
            plan = StudyPlanResult(**data)
        except ValidationError as exc:
            # Summarise Pydantic errors into a human-readable string for the
            # correction prompt — keeps the correction concise.
            errors = "; ".join(
                f"{' → '.join(str(loc) for loc in e['loc'])}: {e['msg']}"
                for e in exc.errors()
            )
            return None, f"Schema validation failed: {errors}"

        # Step 3 — business-rule checks not covered by Pydantic constraints
        if plan.estimated_days != len(plan.study_plan):
            # Tolerate the mismatch by silently correcting estimated_days
            # rather than triggering an expensive retry — the day objects are
            # what the client actually uses.
            logger.warning(
                "estimated_days=%d does not match study_plan length=%d — auto-correcting.",
                plan.estimated_days,
                len(plan.study_plan),
            )
            # Re-construct with corrected value (StudyPlanResult is a Pydantic model)
            corrected_data = data.copy()
            corrected_data["estimated_days"] = len(plan.study_plan)
            plan = StudyPlanResult(**corrected_data)

        if not plan.topic.strip():
            return None, "Field 'topic' must not be empty."

        for day in plan.study_plan:
            if not day.focus.strip():
                return None, f"Day {day.day} has an empty 'focus' field."
            if not day.tasks:
                return None, f"Day {day.day} has no tasks."

        return plan, ""

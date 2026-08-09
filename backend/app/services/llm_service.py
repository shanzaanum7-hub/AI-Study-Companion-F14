"""
LLM Service

Provides a unified interface for chat-completion and text-generation
across multiple LLM providers: OpenAI, Anthropic, Ollama, and Gemini.

The active provider is selected via the ``LLM_PROVIDER`` config setting.
No business logic lives here — only provider abstraction and prompt formatting.

Provider map
────────────
  "openai"    → OpenAIProvider    (OpenAI Chat Completions API)
  "anthropic" → AnthropicProvider (Anthropic Messages API)
  "ollama"    → OllamaProvider    (local Ollama server)
  "gemini"    → GeminiProvider    (Google Gemini generative API)
"""

from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Response data class
# ---------------------------------------------------------------------------


@dataclass
class LLMResponse:
    """Standardised response returned by any LLM provider."""

    content: str
    """The generated text content."""

    model: str
    """Model identifier that produced the response."""

    tokens_used: Optional[int] = None
    """Total tokens consumed (prompt + completion), if available."""

    finish_reason: Optional[str] = None
    """Stop reason reported by the provider (e.g. 'stop', 'length')."""


# ---------------------------------------------------------------------------
# Message types
# ---------------------------------------------------------------------------


@dataclass
class Message:
    """A single chat message."""

    role: str
    """One of: 'system', 'user', 'assistant'."""

    content: str
    """Text content of the message."""


# ---------------------------------------------------------------------------
# Abstract base provider
# ---------------------------------------------------------------------------


class BaseLLMProvider(ABC):
    """Interface that every LLM provider must implement."""

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send a chat-completion request and return the response.

        Args:
            messages:    Ordered conversation history.
            temperature: Sampling temperature override.
            max_tokens:  Max tokens override.

        Returns:
            :class:`LLMResponse` with the generated content.
        """

    @abstractmethod
    def ping(self) -> bool:
        """Return True if the provider is reachable."""


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------


class OpenAIProvider(BaseLLMProvider):
    """LLM provider backed by the OpenAI Chat Completions API."""

    def __init__(self) -> None:
        try:
            from openai import OpenAI  # type: ignore

            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError as exc:
            raise RuntimeError(
                "openai package is required. Install with: pip install openai"
            ) from exc

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        oai_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=oai_messages,
            temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            tokens_used=usage.total_tokens if usage else None,
            finish_reason=choice.finish_reason,
        )

    def ping(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception as exc:
            logger.warning("OpenAI ping failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------


class AnthropicProvider(BaseLLMProvider):
    """LLM provider backed by the Anthropic Messages API."""

    def __init__(self) -> None:
        try:
            import anthropic  # type: ignore

            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        except ImportError as exc:
            raise RuntimeError(
                "anthropic package is required. Install with: pip install anthropic"
            ) from exc

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        # Anthropic separates the system prompt from the conversation
        system_prompt = ""
        conversation: List[dict] = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                conversation.append({"role": m.role, "content": m.content})

        response = self._client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            system=system_prompt or None,
            messages=conversation,
            temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        content_text = "".join(
            block.text for block in response.content if hasattr(block, "text")
        )
        return LLMResponse(
            content=content_text,
            model=response.model,
            tokens_used=(response.usage.input_tokens + response.usage.output_tokens),
            finish_reason=response.stop_reason,
        )

    def ping(self) -> bool:
        try:
            # Anthropic has no explicit "ping" endpoint; try a minimal request
            self._client.models.list()
            return True
        except Exception as exc:
            logger.warning("Anthropic ping failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------


class OllamaProvider(BaseLLMProvider):
    """LLM provider backed by a locally running Ollama server."""

    def __init__(self) -> None:
        try:
            import httpx  # type: ignore

            self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
            self._http = httpx.Client(timeout=120.0)
        except ImportError as exc:
            raise RuntimeError(
                "httpx is required for Ollama provider. Install with: pip install httpx"
            ) from exc

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
                "num_predict": max_tokens or settings.LLM_MAX_TOKENS,
            },
        }
        response = self._http.post(f"{self._base_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", settings.OLLAMA_MODEL),
            finish_reason=data.get("done_reason"),
        )

    def ping(self) -> bool:
        try:
            resp = self._http.get(f"{self._base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception as exc:
            logger.warning("Ollama ping failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Gemini provider
# ---------------------------------------------------------------------------


class GeminiProvider(BaseLLMProvider):
    """
    LLM provider backed by the Google Gemini generative API.

    Uses ``google-generativeai`` under the hood — the same SDK already
    used by the embedding service, so no extra dependency is needed.

    Environment variables
    ─────────────────────
    GEMINI_API_KEY          Google AI Studio API key (required)
    GEMINI_CHAT_MODEL       Model name (default: gemini-1.5-flash)
    LLM_TEMPERATURE         Sampling temperature (shared setting)
    LLM_MAX_TOKENS          Max output tokens (shared setting)
    GEMINI_MAX_RETRIES      Retry attempts on transient errors (default: 3)
    GEMINI_RETRY_BACKOFF    Seconds between retries (default: 2)
    """

    def __init__(self) -> None:
        try:
            import google.generativeai as genai  # type: ignore
            from google.api_core.exceptions import (  # type: ignore
                DeadlineExceeded,
                PermissionDenied,
                ResourceExhausted,
                ServiceUnavailable,
                Unauthenticated,
            )

            self._genai = genai
            self._transient_errors = (
                ResourceExhausted,
                DeadlineExceeded,
                ServiceUnavailable,
            )
            self._auth_errors = (Unauthenticated, PermissionDenied)
        except ImportError as exc:
            raise RuntimeError(
                "google-generativeai is required for the Gemini provider. "
                "Install with: pip install google-generativeai"
            ) from exc

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        genai.configure(api_key=api_key)

        self._model_name: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
        self._max_retries: int = int(os.getenv("GEMINI_MAX_RETRIES", 3))
        self._retry_backoff: float = float(os.getenv("GEMINI_RETRY_BACKOFF", 2))

        logger.info("GeminiProvider initialised with model: %s", self._model_name)

    # ------------------------------------------------------------------
    # BaseLLMProvider interface
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send a multi-turn chat request to the Gemini API.

        The Gemini SDK uses a different message schema from OpenAI:
          - Roles are ``"user"`` and ``"model"`` (not ``"assistant"``).
          - A ``system`` message has no dedicated role — it is prepended to
            the first ``"user"`` turn as a plain-text prefix.

        Args:
            messages:    Ordered conversation history (:class:`Message` list).
            temperature: Sampling temperature override.
            max_tokens:  Max output tokens override.

        Returns:
            :class:`LLMResponse` with the generated content.

        Raises:
            RuntimeError: After all retry attempts are exhausted.
        """
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tok = max_tokens or settings.LLM_MAX_TOKENS

        genai_messages, system_instruction = self._convert_messages(messages)

        generation_config = self._genai.types.GenerationConfig(
            temperature=temp,
            max_output_tokens=max_tok,
        )

        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_instruction or None,
            generation_config=generation_config,
        )

        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = model.generate_content(genai_messages)
                text = response.text or ""

                # Gemini wraps usage in usage_metadata
                tokens_used: Optional[int] = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    tokens_used = (
                        response.usage_metadata.prompt_token_count
                        + response.usage_metadata.candidates_token_count
                    )

                return LLMResponse(
                    content=text,
                    model=self._model_name,
                    tokens_used=tokens_used,
                    finish_reason=self._extract_finish_reason(response),
                )

            except self._auth_errors as exc:
                # Auth errors are not retryable
                raise RuntimeError(
                    f"Gemini authentication failed — check GEMINI_API_KEY: {exc}"
                ) from exc

            except self._transient_errors as exc:
                last_exc = exc
                logger.warning(
                    "Gemini transient error (attempt %d/%d): %s — retrying in %.1fs",
                    attempt,
                    self._max_retries,
                    exc,
                    self._retry_backoff * attempt,
                )
                time.sleep(self._retry_backoff * attempt)

            except Exception as exc:
                last_exc = exc
                logger.error(
                    "Unexpected Gemini error (attempt %d/%d): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                time.sleep(self._retry_backoff)

        raise RuntimeError(
            f"Gemini API failed after {self._max_retries} attempt(s): {last_exc}"
        ) from last_exc

    def ping(self) -> bool:
        """Return True if the Gemini API is reachable with the configured key."""
        try:
            list(self._genai.list_models())
            return True
        except Exception as exc:
            logger.warning("Gemini ping failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_messages(
        messages: List[Message],
    ) -> tuple[list[dict], str]:
        """
        Convert internal :class:`Message` list to the Gemini SDK format.

        Returns:
            (gemini_messages, system_instruction_text)
            ``gemini_messages`` uses ``"user"`` / ``"model"`` roles.
            ``system_instruction_text`` is the concatenated content of all
            system messages (Gemini handles system prompts at the model level).
        """
        system_parts: list[str] = []
        gemini_messages: list[dict] = []

        for msg in messages:
            if msg.role == "system":
                system_parts.append(msg.content)
            elif msg.role in ("user", "human"):
                gemini_messages.append({"role": "user", "parts": [msg.content]})
            elif msg.role in ("assistant", "model"):
                gemini_messages.append({"role": "model", "parts": [msg.content]})
            else:
                # Treat any unknown role as a user turn
                gemini_messages.append({"role": "user", "parts": [msg.content]})

        # Gemini requires the conversation to start with a user turn
        if gemini_messages and gemini_messages[0]["role"] != "user":
            gemini_messages.insert(
                0, {"role": "user", "parts": ["Please respond to the following."]}
            )

        return gemini_messages, "\n\n".join(system_parts)

    @staticmethod
    def _extract_finish_reason(response) -> Optional[str]:
        """Safely extract finish_reason from a Gemini response object."""
        try:
            candidate = response.candidates[0]
            reason = candidate.finish_reason
            # Gemini returns an enum — convert to string name
            return reason.name if hasattr(reason, "name") else str(reason)
        except (AttributeError, IndexError):
            return None


# ---------------------------------------------------------------------------
# LLM Service facade
# ---------------------------------------------------------------------------


class LLMService:
    """
    Facade that routes requests to the configured LLM provider.

    The provider is selected once at construction time based on
    ``settings.LLM_PROVIDER``.  Swap providers by changing the env var.
    """

    _PROVIDER_MAP = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,
    }

    def __init__(self, provider: Optional[str] = None) -> None:
        provider_name = (provider or settings.LLM_PROVIDER).lower()
        provider_cls = self._PROVIDER_MAP.get(provider_name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown LLM provider '{provider_name}'. "
                f"Choose from: {', '.join(self._PROVIDER_MAP)}"
            )
        self._provider: BaseLLMProvider = provider_cls()
        logger.info("LLMService initialised with provider: %s", provider_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send a chat-completion request through the active provider.

        Args:
            messages:    Ordered conversation history.
            temperature: Optional temperature override.
            max_tokens:  Optional max-tokens override.

        Returns:
            :class:`LLMResponse` with the generated content.
        """
        logger.debug(
            "LLMService.chat: %d message(s), temperature=%s, max_tokens=%s",
            len(messages),
            temperature,
            max_tokens,
        )
        return self._provider.chat(messages, temperature=temperature, max_tokens=max_tokens)

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Convenience wrapper for single-turn text completion.

        Args:
            prompt:        User prompt string.
            system_prompt: Optional system instruction.
            temperature:   Optional temperature override.
            max_tokens:    Optional max-tokens override.

        Returns:
            :class:`LLMResponse` with the generated content.
        """
        messages: List[Message] = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens)

    def ping(self) -> bool:
        """Return True if the active provider is reachable."""
        return self._provider.ping()

"""
LLM Service

Provides a unified interface for chat-completion and text-generation
across multiple LLM providers: OpenAI, Anthropic, and Ollama.

The active provider is selected via the ``LLM_PROVIDER`` config setting.
No business logic lives here — only provider abstraction and prompt formatting.
"""

from __future__ import annotations

import logging
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

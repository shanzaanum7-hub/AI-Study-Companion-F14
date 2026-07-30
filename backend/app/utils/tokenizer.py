"""
Tokenizer utilities.

Thin wrappers around tiktoken (OpenAI-compatible tokenizer) and a simple
whitespace-based fallback. Used by the chunking service to measure token counts
without loading a full embedding model.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional tiktoken import (graceful fallback if not installed)
# ---------------------------------------------------------------------------
try:
    import tiktoken  # type: ignore

    _TIKTOKEN_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TIKTOKEN_AVAILABLE = False
    logger.warning(
        "tiktoken is not installed. Falling back to whitespace-based token counting. "
        "Install it with: pip install tiktoken"
    )


# ---------------------------------------------------------------------------
# Encoder factory
# ---------------------------------------------------------------------------


@lru_cache(maxsize=4)
def get_encoder(model: str = "cl100k_base"):
    """
    Return a cached tiktoken encoder for the given model or encoding name.

    ``cl100k_base`` is used by text-embedding-3-* and GPT-4 family models.

    Args:
        model: A tiktoken encoding name (e.g. 'cl100k_base') or an OpenAI
               model name (e.g. 'gpt-4o').

    Returns:
        A tiktoken ``Encoding`` object, or None if tiktoken is unavailable.
    """
    if not _TIKTOKEN_AVAILABLE:
        return None
    try:
        return tiktoken.get_encoding(model)
    except Exception:
        try:
            return tiktoken.encoding_for_model(model)
        except Exception as exc:
            logger.warning("Could not load tiktoken encoder '%s': %s", model, exc)
            return None


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count the number of tokens in *text*.

    Uses tiktoken when available; falls back to a simple whitespace split.

    Args:
        text:  Input string to tokenize.
        model: Tiktoken encoding or model name.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0

    encoder = get_encoder(model)
    if encoder is not None:
        return len(encoder.encode(text))

    # Whitespace-based fallback: split on any whitespace sequence
    return len(re.split(r"\s+", text.strip()))


def truncate_to_tokens(text: str, max_tokens: int, model: str = "cl100k_base") -> str:
    """
    Truncate *text* so that it contains at most *max_tokens* tokens.

    Args:
        text:       Input string.
        max_tokens: Maximum allowed token count.
        model:      Tiktoken encoding or model name.

    Returns:
        Possibly truncated string. The original string is returned unchanged
        if it is already within the token limit.
    """
    if not text or max_tokens <= 0:
        return ""

    encoder = get_encoder(model)
    if encoder is not None:
        tokens = encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoder.decode(tokens[:max_tokens])

    # Whitespace fallback
    words = re.split(r"(\s+)", text.strip())
    word_tokens = [w for w in words if not re.fullmatch(r"\s+", w)]
    if len(word_tokens) <= max_tokens:
        return text
    return " ".join(word_tokens[:max_tokens])


# ---------------------------------------------------------------------------
# Splitting helpers
# ---------------------------------------------------------------------------


def split_into_token_windows(
    text: str,
    window_size: int,
    overlap: int = 0,
    model: str = "cl100k_base",
) -> List[str]:
    """
    Split *text* into overlapping token windows.

    Args:
        text:        Input string to split.
        window_size: Number of tokens per window.
        overlap:     Number of tokens to overlap between consecutive windows.
        model:       Tiktoken encoding or model name.

    Returns:
        List of text strings, each containing at most *window_size* tokens.

    Raises:
        ValueError: If window_size <= 0 or overlap >= window_size.
    """
    if window_size <= 0:
        raise ValueError("window_size must be a positive integer.")
    if overlap >= window_size:
        raise ValueError("overlap must be strictly less than window_size.")
    if not text.strip():
        return []

    encoder = get_encoder(model)

    if encoder is not None:
        tokens = encoder.encode(text)
        windows: List[str] = []
        step = window_size - overlap
        for start in range(0, len(tokens), step):
            window = tokens[start : start + window_size]
            if not window:
                break
            windows.append(encoder.decode(window))
        return windows

    # Whitespace fallback
    words = re.split(r"\s+", text.strip())
    step = window_size - overlap
    windows = []
    for start in range(0, len(words), step):
        chunk_words = words[start : start + window_size]
        if not chunk_words:
            break
        windows.append(" ".join(chunk_words))
    return windows


# ---------------------------------------------------------------------------
# Sentence-aware splitting helper
# ---------------------------------------------------------------------------


def split_sentences(text: str) -> List[str]:
    """
    Split *text* into sentences using a simple regex heuristic.

    This is intentionally lightweight; for production use, consider spaCy
    or NLTK sentence tokenizers.

    Args:
        text: Input paragraph or document string.

    Returns:
        List of sentence strings, stripped of leading/trailing whitespace.
    """
    # Split on '. ', '! ', '? ' followed by an uppercase letter or end of string
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z\"])", text)
    return [s.strip() for s in raw if s.strip()]

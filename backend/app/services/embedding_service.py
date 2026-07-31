"""
Embedding Service

Converts text strings into dense vector representations using a
sentence-transformer model (or a configurable provider).

The service is intentionally stateless with respect to storage —
it only produces vectors. Persistence is handled by :mod:`qdrant_service`.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Optional sentence-transformers import
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer  # type: ignore

    _ST_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ST_AVAILABLE = False
    logger.warning(
        "sentence-transformers is not installed. Embedding will not work. "
        "Install with: pip install sentence-transformers"
    )


# ---------------------------------------------------------------------------
# Model loader (cached singleton per model name)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=2)
def _load_model(model_name: str) -> "SentenceTransformer":
    """
    Load and cache a SentenceTransformer model by name.

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        Loaded SentenceTransformer instance.

    Raises:
        RuntimeError: If sentence-transformers is not installed.
    """
    if not _ST_AVAILABLE:
        raise RuntimeError(
            "sentence-transformers is required. "
            "Install with: pip install sentence-transformers"
        )
    logger.info("Loading embedding model: %s", model_name)
    model = SentenceTransformer(model_name)
    logger.info("Embedding model loaded: %s", model_name)
    return model


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class EmbeddingService:
    """
    Generates dense vector embeddings for text strings.

    Args:
        model_name:  HuggingFace model identifier (default from settings).
        batch_size:  Number of texts to embed per forward pass.
        normalize:   Whether to L2-normalise output vectors (recommended for
                     cosine similarity).
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        batch_size: int = 32,
        normalize: bool = True,
    ) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.batch_size = batch_size
        self.normalize = normalize
        self._dimension: Optional[int] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single string.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        vectors = self.embed_batch([text])
        return vectors[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of strings in batches.

        Args:
            texts: List of input strings.

        Returns:
            List of embedding vectors, one per input string.

        Raises:
            ValueError: If *texts* is empty.
            RuntimeError: If the model cannot be loaded.
        """
        if not texts:
            raise ValueError("texts must be a non-empty list.")

        model = _load_model(self.model_name)

        logger.debug(
            "Embedding %d text(s) with model '%s'", len(texts), self.model_name
        )

        vectors = model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )

        # Convert numpy array to plain Python lists for JSON serialisability
        return [vec.tolist() for vec in vectors]

    @property
    def dimension(self) -> int:
        """
        Return the output dimensionality of the current embedding model.

        Loads the model on first access; subsequent calls are free.
        """
        if self._dimension is None:
            model = _load_model(self.model_name)
            # SentenceTransformer exposes get_sentence_embedding_dimension()
            self._dimension = model.get_sentence_embedding_dimension()
        return self._dimension  # type: ignore[return-value]

    def get_model_name(self) -> str:
        """Return the active embedding model name."""
        return self.model_name

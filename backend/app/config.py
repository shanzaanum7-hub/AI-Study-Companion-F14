"""
Application configuration using Pydantic Settings.
All settings are loaded from environment variables or the .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Central configuration for the AI Study Companion backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = Field(default="AI Study Companion", description="Human-readable app title")
    APP_VERSION: str = Field(default="0.1.0", description="Semantic version string")
    APP_DESCRIPTION: str = Field(
        default="A production-ready backend for an AI-powered study companion.",
        description="Short description shown in API docs",
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment: development | staging | production")

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    HOST: str = Field(default="0.0.0.0", description="Uvicorn bind host")
    PORT: int = Field(default=8000, description="Uvicorn bind port")

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="List of allowed CORS origins",
    )
    ALLOWED_METHODS: List[str] = Field(default=["*"], description="Allowed HTTP methods")
    ALLOWED_HEADERS: List[str] = Field(default=["*"], description="Allowed HTTP headers")
    ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow cookies / auth headers in CORS requests")

    # ------------------------------------------------------------------
    # File Upload
    # ------------------------------------------------------------------
    UPLOAD_DIR: Path = Field(
        default=BASE_DIR / "uploads",
        description="Directory where uploaded files are stored",
    )
    MAX_UPLOAD_SIZE_MB: int = Field(default=20, description="Maximum upload file size in megabytes")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["pdf"],
        description="Permitted file extensions for upload",
    )

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------
    CHUNK_SIZE: int = Field(default=512, description="Target token size per text chunk")
    CHUNK_OVERLAP: int = Field(default=64, description="Token overlap between consecutive chunks")

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace model identifier used to generate embeddings",
    )
    EMBEDDING_DIMENSION: int = Field(default=384, description="Output dimensionality of the embedding model")

    # ------------------------------------------------------------------
    # Qdrant
    # ------------------------------------------------------------------
    QDRANT_HOST: str = Field(default="localhost", description="Qdrant server host")
    QDRANT_PORT: int = Field(default=6333, description="Qdrant server gRPC/REST port")
    QDRANT_COLLECTION_NAME: str = Field(default="study_documents", description="Default Qdrant collection")
    QDRANT_API_KEY: str | None = Field(default=None, description="Optional Qdrant Cloud API key")

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    LLM_PROVIDER: str = Field(default="openai", description="LLM provider: openai | anthropic | ollama")
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI chat model identifier")
    ANTHROPIC_API_KEY: str | None = Field(default=None, description="Anthropic API key")
    ANTHROPIC_MODEL: str = Field(default="claude-3-haiku-20240307", description="Anthropic model identifier")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama base URL")
    OLLAMA_MODEL: str = Field(default="llama3", description="Ollama model name")
    LLM_TEMPERATURE: float = Field(default=0.2, description="Sampling temperature for generation")
    LLM_MAX_TOKENS: int = Field(default=1024, description="Maximum tokens to generate per response")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    RETRIEVAL_TOP_K: int = Field(default=5, description="Number of chunks returned per similarity search")
    RETRIEVAL_SCORE_THRESHOLD: float = Field(default=0.5, description="Minimum similarity score to include a result")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = Field(default="INFO", description="Root log level: DEBUG | INFO | WARNING | ERROR | CRITICAL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        description="Python logging format string",
    )

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    @property
    def max_upload_size_bytes(self) -> int:
        """Return MAX_UPLOAD_SIZE_MB converted to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Return True when running in the production environment."""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()

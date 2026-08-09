from __future__ import annotations

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

import fitz
import httpx
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

load_dotenv()

logger = logging.getLogger(__name__)

COLLECTION_NAME = "study_notes"
MAX_CHARS_PER_CHUNK = 2000


def _setting(settings: Any, name: str, default: Any = None) -> Any:
    """Get setting from Pydantic settings or environment variables."""
    value = getattr(settings, name, None)

    if value is not None and value != "":
        return value

    return os.getenv(name, default)


def extract_text(file_path: Path) -> tuple[str, int]:
    """Extract text from PDF or TXT."""
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
        return text.strip(), 1

    if suffix == ".pdf":
        pages_text: list[str] = []

        with fitz.open(file_path) as document:
            for page in document:
                pages_text.append(page.get_text())

            page_count = len(document)

        return "\n\n".join(pages_text).strip(), page_count

    raise ValueError("Only PDF and TXT files are supported.")


def _split_long_text(text: str) -> list[str]:
    """Split very long text by words."""
    words = text.split()
    parts: list[str] = []
    current: list[str] = []
    current_length = 0

    for word in words:
        new_length = current_length + len(word) + 1

        if current and new_length > MAX_CHARS_PER_CHUNK:
            parts.append(" ".join(current))
            current = [word]
            current_length = len(word)
        else:
            current.append(word)
            current_length = new_length

    if current:
        parts.append(" ".join(current))

    return parts


def create_chunks(text: str) -> list[str]:
    """
    Create meaningful chunks.

    Paragraphs are preferred. Long paragraphs are split by sentences,
    then by words if necessary.
    """
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHARS_PER_CHUNK:
            sentences = re.split(r"(?<=[.!?۔])\s+", paragraph)
        else:
            sentences = [paragraph]

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            if len(sentence) > MAX_CHARS_PER_CHUNK:
                sentence_parts = _split_long_text(sentence)
            else:
                sentence_parts = [sentence]

            for part in sentence_parts:
                new_length = current_length + len(part) + 2

                if current_parts and new_length > MAX_CHARS_PER_CHUNK:
                    chunks.append("\n\n".join(current_parts))
                    current_parts = [part]
                    current_length = len(part)
                else:
                    current_parts.append(part)
                    current_length = new_length

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return [chunk.strip() for chunk in chunks if chunk.strip()]


async def _generate_embeddings(
    texts: list[str],
    api_key: str,
    model: str,
) -> list[list[float]]:
    """Generate Gemini embeddings using the REST API."""
    model = model.removeprefix("models/")
    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:embedContent"
    )

    embeddings: list[list[float]] = []

    timeout = httpx.Timeout(60.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for index, text in enumerate(texts):
            payload = {
                "model": f"models/{model}",
                "content": {
                    "parts": [
                        {
                            "text": text,
                        }
                    ]
                },
            }

            last_error: Exception | None = None

            for attempt in range(3):
                try:
                    response = await client.post(
                        url,
                        params={"key": api_key},
                        json=payload,
                    )

                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise RuntimeError(
                            f"Gemini temporary error: HTTP {response.status_code}"
                        )

                    response.raise_for_status()

                    data = response.json()
                    values = data.get("embedding", {}).get("values")

                    if not values:
                        raise RuntimeError(
                            "Gemini response did not contain embedding values."
                        )

                    embeddings.append([float(value) for value in values])

                    logger.info(
                        "Generated embedding %d/%d; dimension=%d",
                        index + 1,
                        len(texts),
                        len(values),
                    )

                    break

                except Exception as exc:
                    last_error = exc

                    if attempt < 2:
                        import asyncio

                        await asyncio.sleep(2**attempt)

            else:
                raise RuntimeError(
                    f"Could not generate embedding for chunk {index + 1}: "
                    f"{last_error}"
                )

    return embeddings


def _create_qdrant_client(settings: Any) -> QdrantClient:
    """Create a local or cloud Qdrant client."""
    qdrant_url = _setting(
        settings,
        "QDRANT_URL",
        "http://localhost:6333",
    )

    qdrant_api_key = _setting(settings, "QDRANT_API_KEY", None)

    if qdrant_api_key:
        return QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
        )

    return QdrantClient(url=qdrant_url)


def _get_vector_size(collection_info: Any) -> int | None:
    """Read vector size from Qdrant collection information."""
    vectors = collection_info.config.params.vectors

    if isinstance(vectors, dict):
        first_vector = next(iter(vectors.values()))
        return getattr(first_vector, "size", None)

    return getattr(vectors, "size", None)


def _ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
) -> None:
    """Create the collection if required and validate its dimension."""
    collections = client.get_collections().collections
    exists = any(item.name == collection_name for item in collections)

    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        logger.info(
            "Created Qdrant collection '%s' with dimension %d",
            collection_name,
            vector_size,
        )
        return

    collection_info = client.get_collection(collection_name)
    existing_size = _get_vector_size(collection_info)

    if existing_size is not None and existing_size != vector_size:
        raise ValueError(
            f"Embedding dimension mismatch. "
            f"Qdrant collection uses {existing_size}, "
            f"but current embedding model returns {vector_size}."
        )


async def ingest_document(
    file_path: Path,
    document_id: uuid.UUID,
    settings: Any,
) -> dict[str, Any]:
    """
    Complete ingestion pipeline:

    file → text → chunks → embeddings → Qdrant
    """
    text, pages = extract_text(file_path)

    if not text.strip():
        raise ValueError("The uploaded document contains no readable text.")

    chunks = create_chunks(text)

    if not chunks:
        raise ValueError("No meaningful chunks could be created.")

    logger.info(
        "Document %s: text_length=%d, chunks=%d, pages=%d",
        document_id,
        len(text),
        len(chunks),
        pages,
    )

    api_key = _setting(settings, "GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to backend/.env."
        )

    embedding_model = _setting(
        settings,
        "GEMINI_EMBEDDING_MODEL",
        "gemini-embedding-001",
    )

    embeddings = await _generate_embeddings(
        texts=chunks,
        api_key=api_key,
        model=embedding_model,
    )

    if not embeddings:
        raise RuntimeError("No embeddings were generated.")

    dimension = len(embeddings[0])
    qdrant = _create_qdrant_client(settings)

    collection_name = _setting(
        settings,
        "QDRANT_COLLECTION",
        COLLECTION_NAME,
    )

    _ensure_collection(
        client=qdrant,
        collection_name=collection_name,
        vector_size=dimension,
    )

    points: list[PointStruct] = []

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = f"{document_id}_{index}"

        # UUID is accepted by Qdrant as a valid point ID.
        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                chunk_id,
            )
        )

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "document_id": str(document_id),
                    "chunk_id": chunk_id,
                    "chunk_index": index,
                    "text": chunk,
                },
            )
        )

    qdrant.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )

    logger.info(
        "Document %s: upserted %d vectors into '%s'",
        document_id,
        len(points),
        collection_name,
    )

    return {
        "pages": pages,
        "text_length": len(text),
        "chunks": len(chunks),
        "embedding_dimension": dimension,
        "collection": collection_name,
    }


def delete_document_vectors(
    document_id: uuid.UUID,
    settings: Any,
) -> None:
    """Delete all Qdrant points belonging to a document."""
    qdrant = _create_qdrant_client(settings)

    collection_name = _setting(
        settings,
        "QDRANT_COLLECTION",
        COLLECTION_NAME,
    )

    collections = qdrant.get_collections().collections

    if not any(item.name == collection_name for item in collections):
        return

    qdrant.delete(
        collection_name=collection_name,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=str(document_id)),
                    )
                ]
            )
        ),
        wait=True,
    )

    logger.info(
        "Deleted vectors for document %s from '%s'",
        document_id,
        collection_name,
    )
"""
File-handling utilities.

Provides helpers for validating, saving, and managing uploaded files.
No business logic — pure I/O and validation helpers.
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIME_WHITELIST: dict[str, str] = {
    "application/pdf": "pdf",
}


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_extension(filename: str) -> str:
    """
    Ensure the filename carries an allowed extension.

    Args:
        filename: Original filename from the upload.

    Returns:
        The lower-cased extension (without leading dot).

    Raises:
        HTTPException 415: If the extension is not in ALLOWED_EXTENSIONS.
    """
    suffix = Path(filename).suffix.lstrip(".").lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File type '.{suffix}' is not supported. "
                f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            ),
        )
    return suffix


def validate_content_type(upload_file: UploadFile) -> None:
    """
    Verify the MIME type reported by the client is in the whitelist.

    Args:
        upload_file: The FastAPI UploadFile object.

    Raises:
        HTTPException 415: If the content type is not allowed.
    """
    content_type = upload_file.content_type or ""
    # Strip parameters, e.g. "application/pdf; charset=utf-8" → "application/pdf"
    base_type = content_type.split(";")[0].strip().lower()
    if base_type not in MIME_WHITELIST:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"MIME type '{base_type}' is not allowed.",
        )


async def validate_file_size(upload_file: UploadFile) -> int:
    """
    Read the file into memory to determine its size, then seek back to start.

    Args:
        upload_file: The FastAPI UploadFile object.

    Returns:
        The exact file size in bytes.

    Raises:
        HTTPException 413: If the file exceeds MAX_UPLOAD_SIZE_BYTES.
    """
    contents = await upload_file.read()
    file_size = len(contents)

    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size {file_size / (1024 ** 2):.2f} MB exceeds the "
                f"maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
            ),
        )

    # Seek back so subsequent reads work correctly
    await upload_file.seek(0)
    return file_size


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def build_upload_path(original_filename: str, document_id: uuid.UUID) -> Path:
    """
    Construct a deterministic, collision-free storage path for an uploaded file.

    Files are stored as ``<upload_dir>/<document_id>/<original_filename>``.

    Args:
        original_filename: Sanitised original filename.
        document_id:       UUID assigned to the document.

    Returns:
        Absolute Path object for the target file.
    """
    dest_dir = settings.UPLOAD_DIR / str(document_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir / sanitise_filename(original_filename)


def sanitise_filename(filename: str) -> str:
    """
    Remove unsafe characters from a filename.

    Keeps alphanumerics, hyphens, underscores, and dots.

    Args:
        filename: Raw filename string.

    Returns:
        Safe filename string.
    """
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    safe_stem = "".join(c if (c.isalnum() or c in "-_") else "_" for c in stem)
    return f"{safe_stem}{suffix.lower()}"


async def save_upload_file(upload_file: UploadFile, destination: Path) -> int:
    """
    Stream an uploaded file to disk.

    Args:
        upload_file:  The FastAPI UploadFile to persist.
        destination:  Target Path on disk.

    Returns:
        Number of bytes written.

    Raises:
        HTTPException 500: On any I/O error.
    """
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        bytes_written = 0
        with destination.open("wb") as out_file:
            while chunk := await upload_file.read(1024 * 256):  # 256 KB chunks
                out_file.write(chunk)
                bytes_written += len(chunk)
        logger.info("Saved upload to '%s' (%d bytes)", destination, bytes_written)
        return bytes_written
    except OSError as exc:
        logger.exception("Failed to save file to '%s': %s", destination, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist uploaded file.",
        ) from exc


def delete_upload(document_id: uuid.UUID) -> bool:
    """
    Remove the directory and all files associated with a document.

    Args:
        document_id: The document whose uploads should be removed.

    Returns:
        True if the directory existed and was removed; False otherwise.
    """
    target_dir = settings.UPLOAD_DIR / str(document_id)
    if target_dir.exists():
        shutil.rmtree(target_dir)
        logger.info("Deleted upload directory: %s", target_dir)
        return True
    logger.warning("Upload directory not found for document %s", document_id)
    return False


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------


async def compute_sha256(upload_file: UploadFile) -> Tuple[str, int]:
    """
    Compute the SHA-256 digest and byte size of an upload without storing it.

    Seeks back to the beginning of the file after reading.

    Args:
        upload_file: The FastAPI UploadFile to hash.

    Returns:
        Tuple of (hex_digest, file_size_bytes).
    """
    hasher = hashlib.sha256()
    total = 0
    await upload_file.seek(0)
    while chunk := await upload_file.read(1024 * 256):
        hasher.update(chunk)
        total += len(chunk)
    await upload_file.seek(0)
    return hasher.hexdigest(), total


# ---------------------------------------------------------------------------
# MIME detection fallback
# ---------------------------------------------------------------------------


def guess_mime_type(filename: str) -> str:
    """
    Guess the MIME type of a file based on its extension.

    Args:
        filename: Filename or path string.

    Returns:
        MIME type string, defaulting to 'application/octet-stream'.
    """
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"

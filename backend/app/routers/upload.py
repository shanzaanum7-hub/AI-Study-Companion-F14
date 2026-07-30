"""
Upload Router

Handles all file-upload operations:
  POST   /upload            – upload and queue a PDF for processing
  GET    /upload/{doc_id}   – get document status / metadata
  DELETE /upload/{doc_id}   – remove a document and its vectors
  GET    /upload            – list uploaded documents
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.config import Settings, get_settings
from app.models.response_models import APIResponse, DocumentResponse, UploadResponse
from app.models.schemas import LanguageCode, UploadMetadataSchema
from app.utils.file_handler import (
    build_upload_path,
    compute_sha256,
    save_upload_file,
    validate_content_type,
    validate_extension,
    validate_file_size,
    delete_upload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def get_settings_dep() -> Settings:
    return get_settings()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    summary="Upload a PDF document",
    description=(
        "Accept a PDF file and optional metadata. "
        "The file is validated, stored, and queued for chunking + indexing."
    ),
    response_model=APIResponse[UploadResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF file to upload")],
    title: Annotated[Optional[str], Form(description="Document title")] = None,
    subject: Annotated[Optional[str], Form(description="Subject or topic")] = None,
    language: Annotated[LanguageCode, Form(description="Primary language")] = LanguageCode.EN,
    tags: Annotated[Optional[str], Form(description="Comma-separated tags")] = None,
    settings: Settings = Depends(get_settings_dep),
) -> APIResponse[UploadResponse]:
    """
    Upload a PDF document for ingestion.

    - Validates file type, MIME, and size.
    - Saves the file to the upload directory.
    - Returns a document ID and ``processing`` status.

    The actual chunking and embedding pipeline is triggered asynchronously
    (background task / worker — wired up when business logic is implemented).
    """
    logger.info("Upload request received: filename=%r", file.filename)

    # 1. Validate extension
    validate_extension(file.filename or "")

    # 2. Validate MIME type
    validate_content_type(file)

    # 3. Validate file size (reads then seeks back to 0)
    file_size = await validate_file_size(file)

    # 4. Parse tags from comma-separated form field
    tag_list: List[str] = []
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]

    # 5. Build metadata schema for validation
    metadata = UploadMetadataSchema(
        title=title,
        subject=subject,
        language=language,
        tags=tag_list,
    )

    # 6. Assign a document ID and compute checksum
    document_id = uuid.uuid4()
    sha256, _ = await compute_sha256(file)
    logger.debug("File SHA-256: %s, size: %d bytes", sha256, file_size)

    # 7. Persist to disk
    destination = build_upload_path(file.filename or "upload.pdf", document_id)
    await save_upload_file(file, destination)

    logger.info(
        "Document %s saved to '%s'. Queuing for processing.",
        document_id,
        destination,
    )

    # 8. TODO: dispatch background ingestion task (pdf → chunk → embed → index)

    return APIResponse(
        success=True,
        message="File uploaded successfully and queued for processing.",
        data=UploadResponse(
            document_id=document_id,
            filename=destination.name,
            status="processing",
            message="Your document is being processed. Use the document ID to check status.",
        ),
    )


@router.get(
    "",
    summary="List uploaded documents",
    description="Return a paginated list of all uploaded documents.",
    response_model=APIResponse[List[dict]],
    status_code=status.HTTP_200_OK,
)
async def list_documents(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    subject: Annotated[Optional[str], Query(description="Filter by subject")] = None,
) -> APIResponse[List[dict]]:
    """
    List all uploaded documents.

    Placeholder — returns an empty list until the persistence layer is wired up.
    """
    logger.info("List documents: page=%d, page_size=%d, subject=%s", page, page_size, subject)

    # TODO: query document metadata store and return real records
    return APIResponse(
        success=True,
        message="Document list retrieved.",
        data=[],
    )


@router.get(
    "/{document_id}",
    summary="Get document status",
    description="Retrieve metadata and processing status for a specific document.",
    response_model=APIResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}},
)
async def get_document(
    document_id: uuid.UUID,
) -> APIResponse[DocumentResponse]:
    """
    Return metadata and processing status for *document_id*.

    Placeholder — raises 404 until the persistence layer is wired up.
    """
    logger.info("Get document: %s", document_id)

    # TODO: query document store for real metadata
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document '{document_id}' not found.",
    )


@router.delete(
    "/{document_id}",
    summary="Delete a document",
    description="Remove a document, its uploaded file, and all indexed vectors.",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}},
)
async def delete_document(
    document_id: uuid.UUID,
) -> APIResponse[dict]:
    """
    Delete a document and all associated data.

    - Removes the uploaded file from disk.
    - TODO: removes vectors from Qdrant.
    - TODO: removes metadata from the document store.
    """
    logger.info("Delete document: %s", document_id)

    # Remove uploaded file from disk (best-effort)
    removed = delete_upload(document_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    # TODO: delete vectors from Qdrant via retrieval_service.delete_document()
    # TODO: delete metadata record from document store

    return APIResponse(
        success=True,
        message=f"Document '{document_id}' deleted successfully.",
        data={"document_id": str(document_id)},
    )

from __future__ import annotations

import hashlib
import logging
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.config import Settings, get_settings
from app.models.response_models import APIResponse, UploadResponse
from app.models.schemas import LanguageCode, UploadMetadataSchema
from app.services.ingestion_service import (
    delete_document_vectors,
    ingest_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])

MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt"}

# Prototype ke liye in-memory status store.
# Server restart hone par ye data reset ho jayega.
DOCUMENTS: dict[str, dict[str, Any]] = {}


def get_settings_dep() -> Settings:
    return get_settings()


def _safe_filename(filename: str) -> str:
    """Prevent path traversal and keep only the file name."""
    name = Path(filename).name.strip()

    if not name:
        return "uploaded_document"

    return name


@router.post(
    "",
    summary="Upload and index a PDF or TXT document",
    description=(
        "Uploads a document, creates chunks, generates embeddings, "
        "and stores vectors in Qdrant."
    ),
    response_model=APIResponse[UploadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[
        UploadFile,
        File(description="PDF or TXT study document"),
    ],
    title: Annotated[str | None, Form()] = None,
    subject: Annotated[str | None, Form()] = None,
    language: Annotated[LanguageCode, Form()] = LanguageCode.EN,
    tags: Annotated[str | None, Form()] = None,
    settings: Settings = Depends(get_settings_dep),
) -> APIResponse[UploadResponse]:
    filename = _safe_filename(file.filename or "")
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF and TXT files are supported.",
        )

    # Metadata validation
    tag_list = [
        item.strip().lower()
        for item in (tags or "").split(",")
        if item.strip()
    ]

    UploadMetadataSchema(
        title=title,
        subject=subject,
        language=language,
        tags=tag_list,
    )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Maximum file size is 20 MB.",
        )

    if suffix == ".pdf" and not file_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF.",
        )

    document_id = uuid.uuid4()

    upload_dir = Path(
        getattr(
            settings,
            "UPLOAD_DIR",
            Path(__file__).resolve().parents[1] / "uploads",
        )
    )
    upload_dir.mkdir(parents=True, exist_ok=True)

    destination = upload_dir / f"{document_id}_{filename}"
    destination.write_bytes(file_bytes)

    sha256 = hashlib.sha256(file_bytes).hexdigest()

    DOCUMENTS[str(document_id)] = {
        "document_id": str(document_id),
        "filename": filename,
        "status": "processing",
        "title": title,
        "subject": subject,
        "language": str(language),
        "tags": tag_list,
        "sha256": sha256,
        "file_size": len(file_bytes),
    }

    logger.info(
        "Saved document %s to %s",
        document_id,
        destination,
    )

    try:
        # Synchronous processing prototype ke liye behtar hai:
        # response tab milega jab Qdrant mein vectors store ho chuke hon.
        result = await ingest_document(
            file_path=destination,
            document_id=document_id,
            settings=settings,
        )

        DOCUMENTS[str(document_id)].update(
            {
                "status": "completed",
                **result,
            }
        )

        logger.info(
            "Document %s indexed successfully.",
            document_id,
        )

        return APIResponse(
            success=True,
            message="File uploaded and indexed successfully.",
            data=UploadResponse(
                document_id=document_id,
                filename=filename,
                status="completed",
                message=(
                    f"Created {result['chunks']} chunks and stored "
                    f"{result['chunks']} vectors in Qdrant."
                ),
            ),
        )

    except Exception as exc:
        DOCUMENTS[str(document_id)]["status"] = "failed"
        DOCUMENTS[str(document_id)]["error"] = str(exc)

        logger.exception(
            "Ingestion failed for document %s",
            document_id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "File was saved, but indexing failed. "
                "Check the FastAPI terminal logs."
            ),
        ) from exc


@router.get(
    "",
    summary="List uploaded documents",
    response_model=APIResponse[list[dict]],
)
async def list_documents(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    subject: Annotated[str | None, Query()] = None,
) -> APIResponse[list[dict]]:
    documents = list(DOCUMENTS.values())

    if subject:
        documents = [
            item
            for item in documents
            if item.get("subject") == subject
        ]

    start = (page - 1) * page_size
    end = start + page_size

    return APIResponse(
        success=True,
        message="Document list retrieved.",
        data=documents[start:end],
    )


@router.get(
    "/{document_id}",
    summary="Get document status",
    response_model=APIResponse[dict],
)
async def get_document(
    document_id: uuid.UUID,
) -> APIResponse[dict]:
    document = DOCUMENTS.get(str(document_id))

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    return APIResponse(
        success=True,
        message="Document status retrieved.",
        data=document,
    )


@router.delete(
    "/{document_id}",
    summary="Delete a document and its vectors",
    response_model=APIResponse[dict],
)
async def delete_document(
    document_id: uuid.UUID,
    settings: Settings = Depends(get_settings_dep),
) -> APIResponse[dict]:
    document_key = str(document_id)
    document = DOCUMENTS.get(document_key)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    try:
        delete_document_vectors(
            document_id=document_id,
            settings=settings,
        )
    except Exception:
        logger.exception(
            "Could not delete Qdrant vectors for %s",
            document_id,
        )

    filename = document.get("filename", "")
    upload_dir = Path(
        getattr(
            settings,
            "UPLOAD_DIR",
            Path(__file__).resolve().parents[1] / "uploads",
        )
    )
    file_path = upload_dir / f"{document_id}_{filename}"

    if file_path.exists():
        file_path.unlink()

    DOCUMENTS.pop(document_key, None)

    return APIResponse(
        success=True,
        message="Document and its vectors deleted successfully.",
        data={"document_id": document_key},
    )
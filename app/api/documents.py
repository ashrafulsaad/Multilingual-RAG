from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.schemas import (
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentProcessingError, DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])
document_service = DocumentService()
documents: dict[str, DocumentMetadata] = {}


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    return DocumentListResponse(documents=list(documents.values()))


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    language_hint: Annotated[str | None, Form()] = None,
) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=422, detail="A filename is required.")

    try:
        content = await file.read()
        document = document_service.save_and_extract(
            filename=file.filename,
            content=content,
            media_type=file.content_type or "application/octet-stream",
            language_hint=language_hint,
        )
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    metadata = DocumentMetadata(
            document_id=document.document_id,
            filename=document.filename,
            media_type=document.media_type,
            size_bytes=document.size_bytes,
            language_hint=document.language_hint,
            extracted_characters=len(document.text),
            stored_path=document.stored_path,
        )
    documents[metadata.document_id] = metadata
    return DocumentUploadResponse(document=metadata)
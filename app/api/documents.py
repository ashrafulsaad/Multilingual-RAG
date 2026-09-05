from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.container import database, retrieval_service
from app.core.dependencies import current_user
from app.models.schemas import (
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from app.services.chunking import chunk_text
from app.services.document_service import DocumentProcessingError, DocumentService
from app.services.embedding_service import EmbeddingUnavailableError

router = APIRouter(prefix="/documents", tags=["documents"])
document_service = DocumentService(get_settings().raw_dir)


@router.get("", response_model=DocumentListResponse)
def list_documents(user: Annotated[dict, Depends(current_user)]) -> DocumentListResponse:
    rows = database.fetchall("SELECT id, filename, media_type, size_bytes, language_hint, extracted_characters, stored_path FROM documents WHERE owner_id = ? ORDER BY created_at DESC", (user["sub"],))
    return DocumentListResponse(documents=[DocumentMetadata(document_id=row["id"], filename=row["filename"], media_type=row["media_type"], size_bytes=row["size_bytes"], language_hint=row["language_hint"], extracted_characters=row["extracted_characters"], stored_path=row["stored_path"]) for row in rows])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    user: Annotated[dict, Depends(current_user)],
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
        chunks = chunk_text(document.text)
        retrieval_service.add_chunks(
            [(document.document_id, document.filename, chunk.index, chunk.language, chunk.text) for chunk in chunks],
            owner_id=user["sub"],
        )
        database.execute("INSERT INTO documents (id, owner_id, filename, media_type, size_bytes, language_hint, extracted_characters, stored_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))", (document.document_id, user["sub"], document.filename, document.media_type, document.size_bytes, document.language_hint, len(document.text), document.stored_path))
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    metadata = DocumentMetadata(
        document_id=document.document_id,
        filename=document.filename,
        media_type=document.media_type,
        size_bytes=document.size_bytes,
        language_hint=document.language_hint,
        extracted_characters=len(document.text),
        stored_path=document.stored_path,
    )
    return DocumentUploadResponse(document=metadata)
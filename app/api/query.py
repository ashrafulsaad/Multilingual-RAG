from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.container import llm_service, retrieval_service
from app.core.dependencies import current_user
from app.models.schemas import LatencyMetrics, QueryRequest, QueryResponse, SourceChunk
from app.services.embedding_service import EmbeddingUnavailableError
from app.services.llm_service import OllamaUnavailableError

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query_documents(request: QueryRequest, user: Annotated[dict, Depends(current_user)]) -> QueryResponse:
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="question must not be blank")

    started = perf_counter()
    retrieval_started = perf_counter()
    try:
        retrieval_service.vector_store.owner_id = user["sub"]
        retrieval_service.vector_store._load()
        sources = retrieval_service.retrieve(request.question, request.top_k)
    except EmbeddingUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    retrieval_ms = (perf_counter() - retrieval_started) * 1000
    if not sources:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No documents have been uploaded.")

    context = "\n\n".join(f"[{source.filename} chunk {source.chunk_index}] {source.text}" for source in sources)
    generation_started = perf_counter()
    try:
        answer = llm_service.generate(request.question, context)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    generation_ms = (perf_counter() - generation_started) * 1000

    return QueryResponse(
        answer=answer,
        sources=[SourceChunk.model_validate(source) for source in sources],
        latency_ms=LatencyMetrics(
            retrieval=retrieval_ms,
            generation=generation_ms,
            total=(perf_counter() - started) * 1000,
        ),
    )
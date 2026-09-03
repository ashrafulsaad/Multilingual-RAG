from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    media_type: str
    size_bytes: int
    language_hint: str | None
    extracted_characters: int
    stored_path: str


class DocumentUploadResponse(BaseModel):
    document: DocumentMetadata


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    language: str
    text: str
    score: float


class LatencyMetrics(BaseModel):
    retrieval: float
    generation: float
    total: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    latency_ms: LatencyMetrics
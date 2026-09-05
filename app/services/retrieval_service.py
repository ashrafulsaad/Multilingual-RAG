import math
from dataclasses import dataclass

from app.services.database import Database
from app.services.embedding_service import EmbeddingProvider


@dataclass(frozen=True)
class StoredChunk:
    document_id: str
    filename: str
    chunk_index: int
    language: str
    text: str
    embedding: list[float]


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    filename: str
    chunk_index: int
    language: str
    text: str
    score: float


class InMemoryVectorStore:
    def __init__(self, database: Database | None = None, owner_id: str | None = None) -> None:
        self._chunks: list[StoredChunk] = []
        self.database = database
        self.owner_id = owner_id
        if database is not None:
            self._load()

    def _load(self) -> None:
        rows = self.database.fetchall(
            "SELECT document_id, filename, chunk_index, language, text, embedding FROM chunks"
            + (" WHERE owner_id = ?" if self.owner_id else ""),
            (self.owner_id,) if self.owner_id else (),
        )
        self._chunks = [StoredChunk(row["document_id"], row["filename"], row["chunk_index"], row["language"], row["text"], self.database.decode_embedding(row["embedding"])) for row in rows]

    def add(self, chunks: list[StoredChunk]) -> None:
        self._chunks.extend(chunks)
        if self.database is not None:
            with self.database.connect() as connection:
                connection.executemany(
                    "INSERT INTO chunks (document_id, owner_id, filename, chunk_index, language, text, embedding) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [(chunk.document_id, self.owner_id, chunk.filename, chunk.chunk_index, chunk.language, chunk.text, self.database.encode_embedding(chunk.embedding)) for chunk in chunks],
                )

    def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        def similarity(chunk: StoredChunk) -> float:
            denominator = math.sqrt(sum(value * value for value in query_embedding)) * math.sqrt(
                sum(value * value for value in chunk.embedding)
            )
            return sum(left * right for left, right in zip(query_embedding, chunk.embedding)) / denominator if denominator else 0.0

        ranked = sorted(self._chunks, key=similarity, reverse=True)[:top_k]
        return [
            RetrievedChunk(
                document_id=chunk.document_id,
                filename=chunk.filename,
                chunk_index=chunk.chunk_index,
                language=chunk.language,
                text=chunk.text,
                score=similarity(chunk),
            )
            for chunk in ranked
        ]

    def clear(self) -> None:
        self._chunks.clear()


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingProvider, vector_store: InMemoryVectorStore) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def add_chunks(self, chunks: list[tuple[str, str, int, str, str]], owner_id: str | None = None) -> None:
        embeddings = self.embedding_service.encode([item[4] for item in chunks])
        self.vector_store.owner_id = owner_id
        self.vector_store.add(
            [StoredChunk(*item, embedding) for item, embedding in zip(chunks, embeddings)]
        )

    def retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        return self.vector_store.search(self.embedding_service.encode([question])[0], top_k)
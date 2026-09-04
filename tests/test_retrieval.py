from typing import ClassVar

from app.services.retrieval_service import InMemoryVectorStore, RetrievalService


class StubEmbedding:
    vectors: ClassVar[dict[str, list[float]]] = {
        "alpha": [1.0, 0.0],
        "beta": [0.0, 1.0],
        "question": [0.9, 0.1],
    }

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self.vectors[text] for text in texts]


def test_retrieval_orders_by_cosine_similarity() -> None:
    service = RetrievalService(StubEmbedding(), InMemoryVectorStore())
    service.add_chunks([
        ("doc-a", "a.txt", 0, "English", "alpha"),
        ("doc-b", "b.txt", 0, "English", "beta"),
    ])

    results = service.retrieve("question", top_k=2)

    assert [item.filename for item in results] == ["a.txt", "b.txt"]
    assert results[0].score > results[1].score
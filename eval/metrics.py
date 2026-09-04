"""Small, explainable metrics for RAG evaluation."""

import re
from statistics import mean


def recall_at_k(results: list[dict], k: int) -> float:
    return mean(any(item.get("chunk_index") == row.get("correct_chunk_index") for item in row["sources"][:k]) for row in results) if results else 0.0


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def keyword_overlap(answer: str, reference: str) -> float:
    expected = set(re.findall(r"\w+", reference.lower()))
    actual = set(re.findall(r"\w+", answer.lower()))
    return len(expected & actual) / len(expected) if expected else 0.0


def hallucination_rate(results: list[dict]) -> float:
    return mean(not row.get("supported", False) for row in results) if results else 0.0
import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    index: int
    language: str


def detect_language(text: str) -> str:
    bangla = len(re.findall(r"[\u0980-\u09ff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if bangla and latin:
        return "Mixed"
    if bangla:
        return "Bangla"
    return "English"


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[TextChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")
    normalized_text = unicodedata.normalize("NFC", text)
    words = normalized_text.split()
    chunks: list[TextChunk] = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(TextChunk(" ".join(chunk_words), len(chunks), detect_language(" ".join(chunk_words))))
        if start + chunk_size >= len(words):
            break
    return chunks
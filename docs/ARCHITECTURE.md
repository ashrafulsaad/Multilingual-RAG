# Architecture

## Pipeline

`POST /documents` validates the extension, stores the original bytes in `data/raw`, extracts TXT or PDF text, normalizes it with Unicode NFC, splits it into overlapping word-token chunks, labels each chunk as Bangla, English, or Mixed, embeds the chunks, and indexes them in an in-memory vector store.

`POST /query` embeds the question, computes cosine similarity against indexed chunks, returns the top-K sources, and sends those sources plus the question to Ollama. The prompt explicitly says to answer only from context and to say it does not know when context is insufficient.

## Design choices

The default `paraphrase-multilingual-MiniLM-L12-v2` model is small enough for a local portfolio project while supporting multilingual semantic similarity, including Bangla and English. The 300-token chunk and 50-token overlap preserve useful local context while limiting prompt size; both are configurable with `RAG_CHUNK_SIZE` and `RAG_CHUNK_OVERLAP`.

The vector store is behind `RetrievalService` and `InMemoryVectorStore`, so FAISS can later replace storage without changing API routes. Ollama is accessed over HTTP and connection, timeout, malformed-response, and HTTP failures are translated to a clean `503` response.

## Bangla support

Bangla plus English multilingual support is the project's central differentiator. Text is read as UTF-8, decoded with an optional UTF-8 BOM, and normalized using NFC rather than destructive ASCII conversion. This preserves Bangla vowel signs and conjunct characters. Language tagging is a lightweight script-count heuristic intended for metadata, not a replacement for a full language classifier.

## Evaluation

The JSONL dataset mixes Bangla and English questions with a reference answer, expected source chunk, and support keywords. `eval/run_eval.py` calls the real API and writes JSON and CSV evidence. Recall@K checks whether the expected chunk index appears in the returned sources. Correctness uses reference keyword overlap, latency reports p50/p95, and hallucination rate checks whether declared support keywords occur in retrieved context. These are deliberately transparent baselines; an LLM-as-judge can be added later for nuanced answer faithfulness.
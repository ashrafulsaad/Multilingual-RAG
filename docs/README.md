# Bangla Multilingual RAG API

Portfolio-grade FastAPI backend for asking questions over Bangla and English TXT/PDF documents. It combines multilingual sentence-transformer embeddings, an in-memory cosine vector store, and a local Ollama model. No paid API or hosted database is required.

## Features

- Multipart TXT/PDF upload with UTF-8 and Bangla Unicode preservation
- Configurable overlapping chunks and language labels
- Multilingual retrieval using `paraphrase-multilingual-MiniLM-L12-v2`
- Grounded Ollama answers with source chunks and latency metrics
- Offline deterministic tests, evaluation metrics, Docker Compose, and CI

## Local setup

Requires Python 3.12. Create an environment and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install Ollama from https://ollama.com/download, then pull a model:

```bash
ollama serve
ollama pull llama3.2:3b
```

Start the API:

```bash
uvicorn app.main:app --reload
```

The first embedding request downloads the configured model. Set `RAG_EMBEDDING_MODEL`, `RAG_OLLAMA_MODEL`, or other `RAG_*` settings in `.env` as needed.

## API

Health:

```bash
curl http://localhost:8000/health
```

Upload:

```bash
curl -F "file=@document.txt" -F "language_hint=mixed" http://localhost:8000/documents
```

Query:

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What does the document say?","top_k":3}'
```

The query response contains `answer`, ranked `sources`, and retrieval, generation, and total latency in milliseconds. Unsupported files and invalid requests return `422`; no indexed documents return `404`; unavailable Ollama returns `503`.

## Tests and evaluation

```bash
pytest -q
ruff check .
python eval/run_eval.py
```

Evaluation writes `eval/results/results.json` and `eval/results/results.csv`. It reports Recall@K, keyword-overlap correctness, hallucination support checks, and p50/p95 latency. A future LLM-as-judge can replace the simple overlap metric without changing the API.

For a complete walkthrough of local setup, manual API testing, pipeline internals, Docker Compose, evaluation, and GitHub Actions setup, see [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md).

## Docker

```bash
docker compose up --build
docker compose exec ollama ollama pull llama3.2:3b
```

The API and Ollama share a private network, and Ollama models persist in the `ollama_models` volume.
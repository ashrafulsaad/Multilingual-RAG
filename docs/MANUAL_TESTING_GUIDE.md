# Manual Testing and Learning Guide

This guide explains how to run the project locally, test each part manually, and understand what happens inside the RAG pipeline.

## 1. What Is Currently Local?

The project files exist in this workspace. They are not currently connected to GitHub because no Git remote is configured. The workflow at `.github/workflows/ci.yml` is therefore not running anywhere yet.

The workflow is a GitHub Actions recipe. After you push this project to a GitHub repository, GitHub will automatically run it for pushes and pull requests targeting `main`:

1. Install Python 3.12.
2. Install `requirements.txt`.
3. Run `ruff check .`.
4. Run `pytest -q`.
5. Build the Docker image.

It does not deploy the application, start Ollama, pull an LLM, or push an image.

## 2. Prerequisites

For automated tests, install Python and the dependencies. Python 3.12 is the project target:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For real RAG queries, also install Docker or Ollama. A native Ollama installation is useful for learning because you can inspect the model directly:

```bash
ollama serve
ollama pull llama3.2:3b
```

The configured defaults are:

| Setting | Default |
| --- | --- |
| Embedding model | `paraphrase-multilingual-MiniLM-L12-v2` |
| Chunk size | `300` words/tokens approximately |
| Chunk overlap | `50` words/tokens approximately |
| Ollama URL | `http://localhost:11434` |
| Ollama model | `llama3.2:3b` |

The embedding model is downloaded by `sentence-transformers` on its first real use, so the first upload can be slow and requires internet access once.

## 3. Start the API

From the repository root:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Keep this terminal open. The API is available at `http://localhost:8000`.

The project now opens a usable document workspace at the root URL. FastAPI also provides interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 4. Test the Health Endpoint

In a second terminal:

```bash
curl -i http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

This route does not contact Ollama or the embedding model. It only proves that FastAPI and Uvicorn are running.

## 5. Upload an English Text Document

Create a small fixture:

```bash
cat > /tmp/english.txt <<'EOF'
The University Library is open from 8 AM to 10 PM.
Students can borrow up to five books for fourteen days.
EOF
```

Upload it:

```bash
curl -s -X POST http://localhost:8000/documents \
  -F "file=@/tmp/english.txt" \
  -F "language_hint=English"
```

Inspect the response. It should contain a generated `document_id`, filename, media type, byte size, extracted character count, and a path under `data/raw`.

Check that the original was persisted:

```bash
find data/raw -type f -maxdepth 1 -print
```

Upload a `.docx` or another unsupported extension to confirm a `422` response:

```bash
printf 'not supported' > /tmp/example.docx
curl -i -X POST http://localhost:8000/documents -F "file=@/tmp/example.docx"
```

## 6. Upload Bangla and Mixed Documents

Use UTF-8 when creating the Bangla fixture:

```bash
printf 'ঢাকা বাংলাদেশের রাজধানী।\nবাংলা ও English একই নথিতে আছে।\n' > /tmp/bangla.txt
curl -s -X POST http://localhost:8000/documents \
  -F "file=@/tmp/bangla.txt" \
  -F "language_hint=Mixed"
```

The text should remain readable in the response-related metadata and in the stored file. The chunk metadata later labels this content `Bangla` or `Mixed` based on Unicode script counts.

For PDF testing, upload any text-based PDF:

```bash
curl -s -X POST http://localhost:8000/documents \
  -F "file=@/path/to/document.pdf"
```

Scanned image-only PDFs do not contain an extractable text layer and will be rejected as empty. OCR is not implemented in this version.

## 7. Ask a Question

Once an upload succeeds, ask a question answered by its contents:

```bash
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"When is the library open?","top_k":3}'
```

Expected response shape:

```json
{
  "answer": "...",
  "sources": [
    {
      "document_id": "...",
      "filename": "english.txt",
      "chunk_index": 0,
      "language": "English",
      "text": "...",
      "score": 0.9
    }
  ],
  "latency_ms": {
    "retrieval": 12.3,
    "generation": 1450.2,
    "total": 1462.8
  }
}
```

Try the same question in Bangla:

```bash
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"বাংলাদেশের রাজধানী কী?","top_k":3}'
```

Ask something absent from the documents. The prompt instructs Ollama to say it does not know instead of inventing an answer. This is a useful hallucination-reduction experiment, but the generated response still depends on the selected local model.

## 8. Understand the Request Path

For an upload:

1. `app/api/documents.py` receives the multipart request.
2. `DocumentService` stores the original and extracts text.
3. `chunk_text` splits normalized text and tags its language.
4. `RetrievalService` embeds and stores each chunk in memory.
5. The API returns document metadata.

For a query:

1. `app/api/query.py` validates the question and `top_k`.
2. The question is embedded with the same embedding service.
3. `InMemoryVectorStore` ranks chunks by cosine similarity.
4. The top chunks are placed into the Ollama prompt.
5. Ollama generates an answer.
6. The API returns the answer, sources, and latency measurements.

The vector store exists only in process memory. Restarting Uvicorn removes the index, even though original files remain in `data/raw`; re-upload documents after a restart.

## 9. Run Automated Tests

```bash
ruff check .
pytest -q
python -m compileall -q app eval scripts
```

The tests intentionally do not require internet, Ollama, or downloaded embedding models. They replace the embedding service with deterministic vectors and replace Ollama with a failure stub where needed. This makes CI reliable and fast.

The tests cover:

- Health response
- Text upload and metadata
- Unsupported upload validation
- Bangla Unicode preservation
- Chunk overlap and language detection
- Deterministic retrieval ordering
- Query validation and Ollama `503` handling

## 10. Run Dataset Cleaning

The cleaner is a standalone CLI. It removes simple HTML/boilerplate, normalizes whitespace and Unicode, skips short records, removes exact duplicates, and writes JSONL:

```bash
python scripts/clean_dataset.py data/raw data/processed/cleaned.jsonl --min-chars 20
```

Inspect the output:

```bash
cat data/processed/cleaned.jsonl
```

## 11. Run Evaluation

Start the API and make sure documents matching your evaluation data are uploaded first. Then run:

```bash
python eval/run_eval.py
```

Results are written to:

- `eval/results/results.json`
- `eval/results/results.csv`

The console reports Recall@3, keyword-overlap correctness, hallucination support rate, and p50/p95 latency. The evaluation is a simple baseline: an LLM-as-judge would be a future improvement for nuanced semantic correctness and faithfulness.

## 12. Test with Docker Compose

Build and start both services:

```bash
docker compose up --build
```

In another terminal, pull the model into the persistent Ollama volume:

```bash
docker compose exec ollama ollama pull llama3.2:3b
```

The API uses `http://ollama:11434` inside the Compose network. Use the same curl commands, targeting `http://localhost:8000`. Stop services with:

```bash
docker compose down
```

The Ollama model remains in the named `ollama_models` volume. The application data is mounted from the local `data` directory.

## 13. Put the Project on GitHub

Create an empty repository on GitHub, then run these commands from `/root/Rag` with your own repository URL:

```bash
git init
git add .
git commit -m "Build Bangla multilingual RAG API"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

After the push, open the repository on GitHub and select the **Actions** tab. The workflow should start automatically. A green run means lint, tests, and the Docker build all passed. A red run means open the failed job to see which step failed.

For future changes:

```bash
git add .
git commit -m "Describe the change"
git push
```

Each push to `main` triggers CI. Pull requests targeting `main` trigger it too.
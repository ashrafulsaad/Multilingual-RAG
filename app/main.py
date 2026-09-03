from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.documents import router as documents_router

app = FastAPI(
    title="Bangla Multilingual RAG API",
    version="0.1.0",
)


app.include_router(documents_router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

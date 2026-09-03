from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.query import router as query_router

app = FastAPI(
    title="Bangla Multilingual RAG API",
    version="0.1.0",
)


app.include_router(documents_router)
app.include_router(query_router)
app.include_router(health_router)
app.mount("/", StaticFiles(directory="app/frontend", html=True), name="frontend")



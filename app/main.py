from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.query import router as query_router
from app.core.config import get_settings

settings = get_settings()
is_production = settings.environment.lower() == "production"

app = FastAPI(
    title="Bangla Multilingual RAG API",
    version="0.1.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)


app.include_router(documents_router)
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(health_router)
app.mount("/", StaticFiles(directory=Path(__file__).parent / "frontend", html=True), name="frontend")



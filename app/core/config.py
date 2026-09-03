from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RAG_", extra="ignore")

    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: int = 300
    chunk_overlap: int = 50
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_timeout_seconds: float = 120.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
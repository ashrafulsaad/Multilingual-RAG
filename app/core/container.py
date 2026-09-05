from app.core.config import get_settings
from app.services.database import Database
from app.services.embedding_service import SentenceTransformerEmbeddingService
from app.services.llm_service import OllamaService
from app.services.retrieval_service import InMemoryVectorStore, RetrievalService

settings = get_settings()
database = Database(settings.database_path)
embedding_service = SentenceTransformerEmbeddingService(settings.embedding_model)
vector_store = InMemoryVectorStore(database)
retrieval_service = RetrievalService(embedding_service, vector_store)
llm_service = OllamaService(settings.ollama_url, settings.ollama_model, settings.ollama_timeout_seconds)
documents: dict[str, object] = {}
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import documents
from app.core.container import retrieval_service
from app.main import app


def auth_headers(client: TestClient) -> dict[str, str]:
    username = f"tester_{id(client)}"
    client.post("/auth/register", json={"username": username, "password": "password123"})
    token = client.post("/auth/login", json={"username": username, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class StubEmbedding:
    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


def test_upload_txt_extracts_unicode_and_returns_metadata(tmp_path: Path, monkeypatch) -> None:
    documents.document_service.raw_dir = tmp_path
    monkeypatch.setattr(retrieval_service, "embedding_service", StubEmbedding())
    client = TestClient(app)
    headers = auth_headers(client)

    response = client.post(
        "/documents",
        files={"file": ("notes.txt", "বাংলা এবং English text", "text/plain")},
        data={"language_hint": "mixed"},
        headers=headers,
    )

    assert response.status_code == 201
    payload = response.json()["document"]
    assert payload["filename"] == "notes.txt"
    assert payload["language_hint"] == "mixed"
    assert payload["extracted_characters"] == len("বাংলা এবং English text")
    assert Path(payload["stored_path"]).read_text(encoding="utf-8") == "বাংলা এবং English text"


def test_upload_rejects_unsupported_file_type(tmp_path: Path, monkeypatch) -> None:
    documents.document_service.raw_dir = tmp_path
    monkeypatch.setattr(retrieval_service, "embedding_service", StubEmbedding())
    client = TestClient(app)
    response = client.post(
        "/documents",
        files={"file": ("notes.docx", b"not supported", "application/octet-stream")},
        headers=auth_headers(client),
    )

    assert response.status_code == 422
    assert "Only .txt and .pdf" in response.json()["detail"]


def test_uploaded_document_is_available_after_refresh(tmp_path: Path, monkeypatch) -> None:
    documents.document_service.raw_dir = tmp_path
    monkeypatch.setattr(retrieval_service, "embedding_service", StubEmbedding())
    client = TestClient(app)
    headers = auth_headers(client)

    upload = client.post(
        "/documents",
        files={"file": ("persistent.txt", "Saved across refreshes", "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 201

    refreshed = client.get("/documents", headers=headers)
    assert refreshed.status_code == 200
    assert [item["filename"] for item in refreshed.json()["documents"]] == ["persistent.txt"]
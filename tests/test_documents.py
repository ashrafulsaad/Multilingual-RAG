from pathlib import Path

from fastapi.testclient import TestClient

from app.api import documents
from app.main import app


def test_upload_txt_extracts_unicode_and_returns_metadata(tmp_path: Path) -> None:
    documents.document_service.raw_dir = tmp_path
    client = TestClient(app)

    response = client.post(
        "/documents",
        files={"file": ("notes.txt", "বাংলা এবং English text", "text/plain")},
        data={"language_hint": "mixed"},
    )

    assert response.status_code == 201
    payload = response.json()["document"]
    assert payload["filename"] == "notes.txt"
    assert payload["language_hint"] == "mixed"
    assert payload["extracted_characters"] == len("বাংলা এবং English text")
    assert Path(payload["stored_path"]).read_text(encoding="utf-8") == "বাংলা এবং English text"


def test_upload_rejects_unsupported_file_type(tmp_path: Path) -> None:
    documents.document_service.raw_dir = tmp_path
    response = TestClient(app).post(
        "/documents",
        files={"file": ("notes.docx", b"not supported", "application/octet-stream")},
    )

    assert response.status_code == 422
    assert "Only .txt and .pdf" in response.json()["detail"]
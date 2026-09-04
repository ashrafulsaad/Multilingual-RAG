from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_root_serves_frontend_workspace() -> None:
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "Ask anything in your library" in response.text
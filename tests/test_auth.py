from fastapi.testclient import TestClient

from app.main import app


def test_register_login_and_protected_documents() -> None:
    client = TestClient(app)
    username = "auth_test_user"
    client.post("/auth/register", json={"username": username, "password": "password123"})
    login = client.post("/auth/login", json={"username": username, "password": "password123"})

    assert login.status_code == 200
    token = login.json()["access_token"]
    assert client.get("/documents").status_code == 401
    assert client.get("/documents", headers={"Authorization": f"Bearer {token}"}).status_code == 200
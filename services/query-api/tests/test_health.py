from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "llm_enabled" in body
    assert "llm_reason" in body
    assert "env_files_checked" in body
import os
import tempfile

from fastapi.testclient import TestClient

os.environ.setdefault("ENABLE_LLM_RAG", "false")
os.environ.setdefault("EMBEDDING_MODEL_NAME", "hashing-local-v1")
os.environ.setdefault("VECTOR_STORE_DIR", tempfile.mkdtemp(prefix="omnistream-query-api-test-"))

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


def test_metrics_endpoint():
    client = TestClient(app)
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "query-api"
    assert "requests_total" in body["counters"]
    assert "http_request_ms" in body["timings_ms"]
    assert body["vector_store"]["model_name"] == "hashing-local-v1"

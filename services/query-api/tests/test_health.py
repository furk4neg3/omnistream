import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import pytest

os.environ.setdefault("ENABLE_LLM_RAG", "false")
os.environ.setdefault("EMBEDDING_MODEL_NAME", "hashing-local-v1")
os.environ.setdefault("VECTOR_STORE_DIR", tempfile.mkdtemp(prefix="omnistream-query-api-test-"))

from app import main as app_main


app = app_main.app


@pytest.fixture(autouse=True)
def reset_app_state():
    original_settings = app_main.settings
    app_main.get_settings.cache_clear()
    app_main.get_query_engine.cache_clear()
    app_main.get_llm_client.cache_clear()

    yield

    app_main.get_settings.cache_clear()
    app_main.get_query_engine.cache_clear()
    app_main.get_llm_client.cache_clear()
    app_main.settings = original_settings


def iso_seconds_ago(seconds: int) -> str:
    return (
        datetime.now(timezone.utc) - timedelta(seconds=seconds)
    ).isoformat().replace("+00:00", "Z")


def configure_status_test_app(
    monkeypatch,
    tmp_path,
    processing_file,
    producer_file,
    dependency_status_max_age_seconds: int = 30,
):
    monkeypatch.setenv("ENABLE_LLM_RAG", "false")
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "hashing-local-v1")
    monkeypatch.setenv("VECTOR_STORE_DIR", str(tmp_path / "vector_store"))
    monkeypatch.setenv("PROCESSING_AGENT_METRICS_FILE", str(processing_file))
    monkeypatch.setenv("PRODUCER_METRICS_FILE", str(producer_file))
    monkeypatch.setenv(
        "DEPENDENCY_STATUS_MAX_AGE_SECONDS",
        str(dependency_status_max_age_seconds),
    )

    app_main.get_settings.cache_clear()
    app_main.get_query_engine.cache_clear()
    app_main.get_llm_client.cache_clear()
    app_main.settings = app_main.get_settings()


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


def test_status_endpoint_with_fresh_running_dependency_metrics(monkeypatch, tmp_path):
    processing_file = tmp_path / "processing-agent-metrics.json"
    producer_file = tmp_path / "producer-metrics.json"
    processing_payload = {
        "service": "processing-agent",
        "status": "running",
        "updated_at": iso_seconds_ago(1),
        "counters": {"polls_total": 2},
    }
    producer_payload = {
        "service": "producer",
        "status": "completed",
        "updated_at": iso_seconds_ago(1),
        "counters": {"events_emitted_total": 3},
    }
    processing_file.write_text(json.dumps(processing_payload), encoding="utf-8")
    producer_file.write_text(json.dumps(producer_payload), encoding="utf-8")
    configure_status_test_app(monkeypatch, tmp_path, processing_file, producer_file)

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "query-api"
    assert body["status"] == "ok"
    assert body["app_name"] == "OmniStream Query API"
    assert body["app_version"] == "0.1.0"
    assert "uptime_seconds" in body
    assert body["vector_store"]["model_name"] == "hashing-local-v1"
    assert body["vector_store"]["record_count"] == 0
    assert body["vector_store"]["embedding_dim"] == 0
    assert body["processing_agent"]["available"] is True
    assert body["processing_agent"]["reason"] is None
    assert body["processing_agent"]["fresh"] is True
    assert body["processing_agent"]["age_seconds"] < 30
    assert body["processing_agent"]["payload"] == processing_payload
    assert body["producer"]["available"] is True
    assert body["producer"]["reason"] is None
    assert body["producer"]["fresh"] is None
    assert body["producer"]["age_seconds"] < 30
    assert body["producer"]["payload"] == producer_payload


def test_status_endpoint_reports_stale_running_dependency_metrics(monkeypatch, tmp_path):
    processing_file = tmp_path / "processing-agent-metrics.json"
    producer_file = tmp_path / "producer-metrics.json"
    processing_payload = {
        "service": "processing-agent",
        "status": "running",
        "updated_at": iso_seconds_ago(120),
        "counters": {"polls_total": 2},
    }
    producer_payload = {
        "service": "producer",
        "status": "completed",
        "updated_at": iso_seconds_ago(120),
        "counters": {"events_emitted_total": 3},
    }
    processing_file.write_text(json.dumps(processing_payload), encoding="utf-8")
    producer_file.write_text(json.dumps(producer_payload), encoding="utf-8")
    configure_status_test_app(
        monkeypatch,
        tmp_path,
        processing_file,
        producer_file,
        dependency_status_max_age_seconds=30,
    )

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == 200
    body = response.json()
    assert body["processing_agent"]["available"] is False
    assert body["processing_agent"]["fresh"] is False
    assert body["processing_agent"]["age_seconds"] >= 120
    assert "stale" in body["processing_agent"]["reason"]
    assert body["processing_agent"]["payload"] == processing_payload


def test_status_endpoint_does_not_mark_old_completed_producer_metrics_stale(monkeypatch, tmp_path):
    processing_file = tmp_path / "processing-agent-metrics.json"
    producer_file = tmp_path / "producer-metrics.json"
    processing_payload = {
        "service": "processing-agent",
        "status": "running",
        "updated_at": iso_seconds_ago(1),
        "counters": {"polls_total": 2},
    }
    producer_payload = {
        "service": "producer",
        "status": "completed",
        "updated_at": iso_seconds_ago(120),
        "counters": {"events_emitted_total": 3},
    }
    processing_file.write_text(json.dumps(processing_payload), encoding="utf-8")
    producer_file.write_text(json.dumps(producer_payload), encoding="utf-8")
    configure_status_test_app(
        monkeypatch,
        tmp_path,
        processing_file,
        producer_file,
        dependency_status_max_age_seconds=30,
    )

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == 200
    body = response.json()
    assert body["producer"]["available"] is True
    assert body["producer"]["reason"] is None
    assert body["producer"]["fresh"] is None
    assert body["producer"]["age_seconds"] >= 120
    assert body["producer"]["payload"] == producer_payload


def test_status_endpoint_when_dependency_metrics_files_are_missing(monkeypatch, tmp_path):
    processing_file = tmp_path / "missing-processing-agent-metrics.json"
    producer_file = tmp_path / "missing-producer-metrics.json"
    configure_status_test_app(monkeypatch, tmp_path, processing_file, producer_file)

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "query-api"
    assert body["processing_agent"]["available"] is False
    assert "not found" in body["processing_agent"]["reason"]
    assert body["processing_agent"]["payload"] is None
    assert body["producer"]["available"] is False
    assert "not found" in body["producer"]["reason"]
    assert body["producer"]["payload"] is None


def test_status_endpoint_when_dependency_metrics_file_contains_invalid_json(monkeypatch, tmp_path):
    processing_file = tmp_path / "processing-agent-metrics.json"
    producer_file = tmp_path / "producer-metrics.json"
    processing_file.write_text("{not-valid-json", encoding="utf-8")
    producer_file.write_text(
        json.dumps(
            {
                "service": "producer",
                "status": "completed",
                "updated_at": iso_seconds_ago(1),
            }
        ),
        encoding="utf-8",
    )
    configure_status_test_app(monkeypatch, tmp_path, processing_file, producer_file)

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == 200
    body = response.json()
    assert body["processing_agent"]["available"] is False
    assert "invalid JSON" in body["processing_agent"]["reason"]
    assert body["processing_agent"]["payload"] is None

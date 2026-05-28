import json
from types import SimpleNamespace

from app.checkpoint import load_checkpoint
from app.processor import ProcessingAgent
from app.vector_store import load_local_vector_store


class FakeEmbedder:
    def encode(self, texts):
        import numpy as np

        rows = []
        for index, text in enumerate(texts, start=1):
            rows.append([float(len(text)), float(index), 1.0])
        return np.array(rows, dtype="float32") if rows else np.empty((0, 0), dtype="float32")


def test_processing_agent_processes_new_events(tmp_path):
    input_file = tmp_path / "events.jsonl"
    output_file = tmp_path / "enriched_events.jsonl"
    checkpoint_file = tmp_path / "state" / "checkpoint.json"
    vector_store_dir = tmp_path / "vector_store"

    event = {
        "event_id": "evt_001",
        "source": "support_ticket",
        "timestamp": "2026-04-12T12:00:00Z",
        "tenant_id": "acme",
        "payload": {
            "ticket_id": "TICK_1001",
            "title": "Checkout timeout on mobile",
            "body": "Users report timeout after entering OTP during mobile checkout.",
            "severity": "high",
            "product": "checkout",
            "customer_tier": "enterprise",
            "language": "en",
            "tags": ["checkout", "mobile", "otp", "timeout"],
        },
    }

    with input_file.open("w", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    settings = SimpleNamespace(
        input_file=str(input_file),
        output_file=str(output_file),
        checkpoint_file=str(checkpoint_file),
        vector_store_dir=str(vector_store_dir),
        batch_size=10,
        chunk_size_words=80,
        chunk_overlap_words=20,
        schema_version="v1",
        processing_version="v1",
        embedding_model_name="test-model",
    )

    agent = ProcessingAgent(settings)
    agent.embedder = FakeEmbedder()

    result = agent.process_once()

    assert result["raw_events_processed"] == 1
    assert result["chunks_written"] >= 1
    assert output_file.exists()

    checkpoint = load_checkpoint(str(checkpoint_file))
    assert checkpoint["lines_processed"] == 1

    embeddings, records, manifest = load_local_vector_store(str(vector_store_dir))
    assert manifest["record_count"] == len(records)
    assert manifest["record_count"] >= 1
    assert embeddings.shape[0] == len(records)
    assert records[0]["ticket_id"] == "TICK_1001"


def test_processing_agent_is_idempotent_with_checkpoint(tmp_path):
    input_file = tmp_path / "events.jsonl"
    output_file = tmp_path / "enriched_events.jsonl"
    checkpoint_file = tmp_path / "state" / "checkpoint.json"
    vector_store_dir = tmp_path / "vector_store"

    event = {
        "event_id": "evt_001",
        "source": "support_ticket",
        "timestamp": "2026-04-12T12:00:00Z",
        "tenant_id": "acme",
        "payload": {
            "ticket_id": "TICK_1001",
            "title": "Checkout timeout on mobile",
            "body": "Users report timeout after entering OTP during mobile checkout.",
            "severity": "high",
            "product": "checkout",
            "customer_tier": "enterprise",
            "language": "en",
            "tags": ["checkout", "mobile", "otp", "timeout"],
        },
    }

    with input_file.open("w", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    settings = SimpleNamespace(
        input_file=str(input_file),
        output_file=str(output_file),
        checkpoint_file=str(checkpoint_file),
        vector_store_dir=str(vector_store_dir),
        batch_size=10,
        chunk_size_words=80,
        chunk_overlap_words=20,
        schema_version="v1",
        processing_version="v1",
        embedding_model_name="test-model",
    )

    agent = ProcessingAgent(settings)
    agent.embedder = FakeEmbedder()

    first = agent.process_once()
    second = agent.process_once()

    assert first["raw_events_processed"] == 1
    assert second["raw_events_processed"] == 0

    _, records, manifest = load_local_vector_store(str(vector_store_dir))
    assert manifest["record_count"] == len(records)
    assert len(records) >= 1


def test_processing_agent_processes_mixed_event_types(tmp_path):
    input_file = tmp_path / "events.jsonl"
    output_file = tmp_path / "enriched_events.jsonl"
    checkpoint_file = tmp_path / "state" / "checkpoint.json"
    vector_store_dir = tmp_path / "vector_store"

    events = [
        {
            "event_id": "evt_ticket_001",
            "source": "support_ticket",
            "timestamp": "2026-04-12T12:00:00Z",
            "tenant_id": "acme",
            "payload": {
                "ticket_id": "TICK_1001",
                "title": "Checkout timeout on mobile",
                "body": "Users report timeout after entering OTP during mobile checkout.",
                "severity": "high",
                "product": "checkout",
                "customer_tier": "enterprise",
                "language": "en",
                "tags": ["checkout", "mobile", "otp", "timeout"],
            },
        },
        {
            "event_id": "evt_chat_001",
            "source": "customer_chat_message",
            "timestamp": "2026-04-12T12:01:00Z",
            "tenant_id": "acme",
            "payload": {
                "conversation_id": "CONV_1001",
                "message_id": "MSG_2001",
                "sender": "customer",
                "message": "Mobile checkout keeps failing after OTP.",
                "severity": "high",
                "product": "checkout",
                "customer_tier": "enterprise",
                "sentiment": "negative",
                "language": "en",
                "tags": ["checkout", "mobile", "otp"],
            },
        },
    ]

    with input_file.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    settings = SimpleNamespace(
        input_file=str(input_file),
        output_file=str(output_file),
        checkpoint_file=str(checkpoint_file),
        vector_store_dir=str(vector_store_dir),
        batch_size=10,
        chunk_size_words=80,
        chunk_overlap_words=20,
        schema_version="v1",
        processing_version="v1",
        embedding_model_name="test-model",
    )

    agent = ProcessingAgent(settings)
    agent.embedder = FakeEmbedder()

    result = agent.process_once()

    assert result["raw_events_processed"] == 2
    assert result["chunks_written"] == 2

    _, records, manifest = load_local_vector_store(str(vector_store_dir))
    assert manifest["record_count"] == 2
    assert {record["metadata"]["event_type"] for record in records} == {
        "support_ticket",
        "customer_chat_message",
    }

import json
from types import SimpleNamespace

from app.observability import AgentMetrics, write_status_file


def test_agent_metrics_snapshot_and_status_file(tmp_path):
    settings = SimpleNamespace(
        input_file="events.jsonl",
        output_file="enriched.jsonl",
        checkpoint_file="checkpoint.json",
        vector_store_dir="vector_store",
        embedding_model_name="hashing-local-v1",
        batch_size=32,
        poll_interval_seconds=1.0,
        loop_forever=True,
    )
    metrics = AgentMetrics(settings)
    metrics.record_result(
        {
            "raw_events_processed": 2,
            "chunks_written": 3,
            "vector_record_count": 3,
            "next_line": 2,
            "event_type_counts": {"support_ticket": 2},
            "chunk_counts_by_event_type": {"support_ticket": 3},
            "router_label_counts": {"support_ticket:v1": 2},
        },
        processing_ms=12.34,
    )
    metrics.record_result(
        {
            "raw_events_processed": 1,
            "chunks_written": 1,
            "vector_record_count": 4,
            "next_line": 3,
            "event_type_counts": {"customer_chat_message": 1},
            "chunk_counts_by_event_type": {"customer_chat_message": 1},
            "router_label_counts": {"customer_chat_message:v1": 1},
        },
        processing_ms=5.67,
    )

    status_file = tmp_path / "state" / "processing-agent-metrics.json"
    write_status_file(str(status_file), metrics.snapshot())

    body = json.loads(status_file.read_text(encoding="utf-8"))
    assert body["service"] == "processing-agent"
    assert body["status"] == "running"
    assert body["counters"]["raw_events_processed_total"] == 3
    assert body["counters"]["chunks_written_total"] == 4
    assert body["route_metrics"] == {
        "events_by_type_total": {
            "support_ticket": 2,
            "customer_chat_message": 1,
        },
        "chunks_by_event_type_total": {
            "support_ticket": 3,
            "customer_chat_message": 1,
        },
        "router_labels_total": {
            "support_ticket:v1": 2,
            "customer_chat_message:v1": 1,
        },
    }
    assert body["last_result"]["processing_ms"] == 5.67
    assert body["last_result"]["event_type_counts"] == {"customer_chat_message": 1}
    assert body["last_result"]["chunk_counts_by_event_type"] == {
        "customer_chat_message": 1,
    }
    assert body["last_result"]["router_label_counts"] == {
        "customer_chat_message:v1": 1,
    }


def test_agent_metrics_lifecycle_status_and_error_precedence():
    settings = SimpleNamespace(
        input_file="events.jsonl",
        output_file="enriched.jsonl",
        checkpoint_file="checkpoint.json",
        vector_store_dir="vector_store",
        embedding_model_name="hashing-local-v1",
        batch_size=32,
        poll_interval_seconds=1.0,
        loop_forever=True,
    )
    metrics = AgentMetrics(settings)

    metrics.set_status("stopping")
    assert metrics.snapshot()["status"] == "stopping"

    metrics.set_status("stopped")
    assert metrics.snapshot()["status"] == "stopped"

    metrics.record_error(RuntimeError("batch failed"))
    snapshot = metrics.snapshot()
    assert snapshot["status"] == "error"
    assert snapshot["counters"]["errors_total"] == 1

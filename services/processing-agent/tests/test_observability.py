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
        },
        processing_ms=12.34,
    )

    status_file = tmp_path / "state" / "processing-agent-metrics.json"
    write_status_file(str(status_file), metrics.snapshot())

    body = json.loads(status_file.read_text(encoding="utf-8"))
    assert body["service"] == "processing-agent"
    assert body["counters"]["raw_events_processed_total"] == 2
    assert body["counters"]["chunks_written_total"] == 3
    assert body["last_result"]["processing_ms"] == 12.34

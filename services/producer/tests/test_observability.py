import json
from types import SimpleNamespace

from app.observability import ProducerMetrics, write_status_file


def test_producer_metrics_snapshot_and_status_file(tmp_path):
    settings = SimpleNamespace(
        output_mode="file",
        output_file="events.jsonl",
        tenant_id="acme",
        enabled_event_types=["support_ticket"],
        events_per_second=1.0,
        max_events=1,
        kinesis_stream_name="omnistream-raw-events",
        aws_region="us-east-1",
    )
    metrics = ProducerMetrics(settings)
    metrics.record_event(
        {
            "event_id": "evt_001",
            "source": "support_ticket",
            "tenant_id": "acme",
            "payload": {"ticket_id": "TICK_001"},
        }
    )

    status_file = tmp_path / "state" / "producer-metrics.json"
    write_status_file(str(status_file), metrics.snapshot(status="completed"))

    body = json.loads(status_file.read_text(encoding="utf-8"))
    assert body["service"] == "producer"
    assert body["status"] == "completed"
    assert body["counters"]["events_emitted_total"] == 1
    assert body["last_event"]["record_id"] == "TICK_001"
    assert body["last_event"]["ticket_id"] == "TICK_001"

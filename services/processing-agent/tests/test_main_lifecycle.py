import json
import os
import signal
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app import main as main_module
from app.observability import write_status_file as real_write_status_file


def _settings(metrics_file):
    return SimpleNamespace(
        input_file="events.jsonl",
        output_file="enriched.jsonl",
        checkpoint_file="checkpoint.json",
        metrics_file=str(metrics_file),
        vector_store_dir="vector_store",
        embedding_model_name="hashing-local-v1",
        batch_size=32,
        poll_interval_seconds=0.01,
        loop_forever=True,
    )


def _empty_result():
    return {
        "raw_events_processed": 0,
        "chunks_written": 0,
        "vector_record_count": 0,
        "next_line": 0,
        "event_type_counts": {},
        "chunk_counts_by_event_type": {},
        "router_label_counts": {},
    }


def test_main_finishes_current_iteration_after_sigterm_then_writes_stopped(
    monkeypatch,
    tmp_path,
):
    metrics_file = tmp_path / "state" / "processing-agent-metrics.json"
    settings = _settings(metrics_file)
    events = []
    status_writes = []
    logs = []

    class FakeProcessingAgent:
        def __init__(self, _settings):
            pass

        def process_once(self):
            events.append("process_started")
            os.kill(os.getpid(), signal.SIGTERM)
            events.append("process_finished")
            return _empty_result()

    def record_status_file(path, payload):
        status_writes.append(deepcopy(payload))
        real_write_status_file(path, payload)

    def record_log(event, **fields):
        logs.append({"event": event, **fields})

    monkeypatch.setattr(main_module, "Settings", lambda: settings)
    monkeypatch.setattr(main_module, "ProcessingAgent", FakeProcessingAgent)
    monkeypatch.setattr(main_module, "write_status_file", record_status_file)
    monkeypatch.setattr(main_module, "log_event", record_log)

    main_module.main()

    assert events == ["process_started", "process_finished"]
    assert [write["status"] for write in status_writes] == [
        "running",
        "stopping",
        "stopping",
        "stopped",
    ]
    assert logs[1] == {
        "event": "processing_shutdown_requested",
        "signal_name": "SIGTERM",
    }

    final_snapshot = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert final_snapshot["status"] == "stopped"
    assert final_snapshot["counters"]["polls_total"] == 1
    assert final_snapshot["counters"]["idle_polls_total"] == 1


def test_main_preserves_error_status_on_batch_failure(monkeypatch, tmp_path):
    metrics_file = tmp_path / "state" / "processing-agent-metrics.json"
    settings = _settings(metrics_file)
    logs = []

    class FailingProcessingAgent:
        def __init__(self, _settings):
            pass

        def process_once(self):
            raise RuntimeError("boom")

    def record_log(event, **fields):
        logs.append({"event": event, **fields})

    monkeypatch.setattr(main_module, "Settings", lambda: settings)
    monkeypatch.setattr(main_module, "ProcessingAgent", FailingProcessingAgent)
    monkeypatch.setattr(main_module, "log_event", record_log)

    with pytest.raises(RuntimeError, match="boom"):
        main_module.main()

    final_snapshot = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert final_snapshot["status"] == "error"
    assert final_snapshot["counters"]["errors_total"] == 1
    assert logs[-1]["event"] == "processing_batch_failed"
    assert logs[-1]["error_type"] == "RuntimeError"

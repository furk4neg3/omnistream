import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


SERVICE_NAME = "processing-agent"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log_event(event: str, level: str = "info", **fields: Any) -> None:
    record = {
        "timestamp": utc_now(),
        "level": level,
        "service": SERVICE_NAME,
        "event": event,
        **fields,
    }
    print(json.dumps(record, default=str, sort_keys=True), flush=True)


class AgentMetrics:
    def __init__(self, settings: Any) -> None:
        self.started_at = utc_now()
        self._started = perf_counter()
        self.counters: defaultdict[str, int] = defaultdict(int)
        self.last_result: dict[str, Any] | None = None
        self.last_error: dict[str, Any] | None = None
        self.config = {
            "input_file": settings.input_file,
            "output_file": settings.output_file,
            "checkpoint_file": settings.checkpoint_file,
            "vector_store_dir": settings.vector_store_dir,
            "embedding_model_name": settings.embedding_model_name,
            "batch_size": settings.batch_size,
            "poll_interval_seconds": settings.poll_interval_seconds,
            "loop_forever": settings.loop_forever,
        }

    def record_result(self, result: dict[str, Any], processing_ms: float) -> None:
        raw_events_processed = int(result.get("raw_events_processed") or 0)
        chunks_written = int(result.get("chunks_written") or 0)

        self.counters["polls_total"] += 1
        self.counters["raw_events_processed_total"] += raw_events_processed
        self.counters["chunks_written_total"] += chunks_written

        if raw_events_processed:
            self.counters["batches_processed_total"] += 1
        else:
            self.counters["idle_polls_total"] += 1

        self.last_result = {
            **result,
            "processing_ms": round(processing_ms, 2),
            "observed_at": utc_now(),
        }

    def record_error(self, error: Exception) -> None:
        self.counters["errors_total"] += 1
        self.last_error = {
            "type": type(error).__name__,
            "message": str(error),
            "observed_at": utc_now(),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "service": SERVICE_NAME,
            "status": "error" if self.last_error else "running",
            "started_at": self.started_at,
            "updated_at": utc_now(),
            "uptime_seconds": round(perf_counter() - self._started, 2),
            "config": self.config,
            "counters": dict(self.counters),
            "last_result": self.last_result,
            "last_error": self.last_error,
        }


def write_status_file(path: str, payload: dict[str, Any]) -> None:
    status_path = Path(path)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    with status_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

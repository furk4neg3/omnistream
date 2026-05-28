import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


SERVICE_NAME = "producer"


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


class ProducerMetrics:
    def __init__(self, settings: Any) -> None:
        self.started_at = utc_now()
        self._started = perf_counter()
        self.counters: defaultdict[str, int] = defaultdict(int)
        self.last_event: dict[str, Any] | None = None
        self.last_error: dict[str, Any] | None = None
        self.config = {
            "output_mode": settings.output_mode,
            "output_file": settings.output_file if settings.output_mode == "file" else None,
            "tenant_id": settings.tenant_id,
            "event_types": settings.enabled_event_types,
            "events_per_second": settings.events_per_second,
            "max_events": settings.max_events,
            "kinesis_stream_name": settings.kinesis_stream_name,
            "aws_region": settings.aws_region,
        }

    def record_event(self, event: dict[str, Any]) -> None:
        payload = event["payload"]
        record_id = payload.get("ticket_id") or payload.get("conversation_id")
        source_payload_id = payload.get("message_id") or payload.get("ticket_id")

        self.counters["events_emitted_total"] += 1
        self.last_event = {
            "event_id": event["event_id"],
            "source": event["source"],
            "record_id": record_id,
            "source_payload_id": source_payload_id,
            "tenant_id": event["tenant_id"],
            "observed_at": utc_now(),
        }

        if event["source"] == "support_ticket":
            self.last_event["ticket_id"] = record_id

    def record_error(self, error: Exception) -> None:
        self.counters["errors_total"] += 1
        self.last_error = {
            "type": type(error).__name__,
            "message": str(error),
            "observed_at": utc_now(),
        }

    def snapshot(self, status: str) -> dict[str, Any]:
        return {
            "service": SERVICE_NAME,
            "status": status,
            "started_at": self.started_at,
            "updated_at": utc_now(),
            "duration_seconds": round(perf_counter() - self._started, 2),
            "config": self.config,
            "counters": dict(self.counters),
            "last_event": self.last_event,
            "last_error": self.last_error,
        }


def write_status_file(path: str, payload: dict[str, Any]) -> None:
    status_path = Path(path)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    with status_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

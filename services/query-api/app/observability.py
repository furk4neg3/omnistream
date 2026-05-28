import json
import threading
from collections import defaultdict
from datetime import datetime, timezone
from time import perf_counter
from typing import Any


SERVICE_NAME = "query-api"


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


class RuntimeMetrics:
    def __init__(self) -> None:
        self.started_at = utc_now()
        self._started = perf_counter()
        self._lock = threading.Lock()
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._timings: defaultdict[str, dict[str, float]] = defaultdict(
            lambda: {"count": 0, "total_ms": 0.0, "max_ms": 0.0}
        )

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] += value

    def observe(self, name: str, duration_ms: float) -> None:
        with self._lock:
            timer = self._timings[name]
            timer["count"] += 1
            timer["total_ms"] += duration_ms
            timer["max_ms"] = max(timer["max_ms"], duration_ms)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            counters = dict(self._counters)
            timings = {
                name: {
                    "count": int(values["count"]),
                    "avg_ms": round(
                        values["total_ms"] / values["count"] if values["count"] else 0.0,
                        2,
                    ),
                    "max_ms": round(values["max_ms"], 2),
                    "total_ms": round(values["total_ms"], 2),
                }
                for name, values in self._timings.items()
            }

        return {
            "started_at": self.started_at,
            "uptime_seconds": round(perf_counter() - self._started, 2),
            "counters": counters,
            "timings_ms": timings,
        }


runtime_metrics = RuntimeMetrics()

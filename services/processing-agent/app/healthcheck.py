import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Settings


DEFAULT_MAX_AGE_SECONDS = 120
MAX_AGE_ENV_VAR = "PROCESSING_AGENT_HEALTHCHECK_MAX_AGE_SECONDS"


def _parse_updated_at(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None

    timestamp = value[:-1] + "+00:00" if value.endswith("Z") else value

    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _metrics_file_path() -> str:
    return os.getenv("METRICS_FILE") or Settings().metrics_file


def _max_age_seconds() -> int:
    raw_value = os.getenv(MAX_AGE_ENV_VAR)
    if raw_value is None:
        return DEFAULT_MAX_AGE_SECONDS

    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_MAX_AGE_SECONDS

    return value if value > 0 else DEFAULT_MAX_AGE_SECONDS


def check_metrics_snapshot(
    path: str,
    max_age_seconds: int,
    now: datetime | None = None,
) -> tuple[bool, str]:
    status_path = Path(path)
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    else:
        current_time = current_time.astimezone(timezone.utc)

    if not status_path.exists():
        return False, f"metrics file not found: {status_path}"

    if not status_path.is_file():
        return False, f"metrics path is not a file: {status_path}"

    try:
        with status_path.open("r", encoding="utf-8") as f:
            payload: Any = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"metrics file contains invalid JSON: {e.msg}"
    except OSError as e:
        return False, f"metrics file is unreadable: {e.strerror or type(e).__name__}"

    if not isinstance(payload, dict):
        return False, "metrics file must contain a JSON object"

    status = payload.get("status")
    if status != "running":
        return False, f'metrics status is not running: {status!r}'

    updated_at = _parse_updated_at(payload.get("updated_at"))
    if updated_at is None:
        return False, "metrics updated_at is missing or unparseable"

    age_seconds = (current_time - updated_at).total_seconds()
    if age_seconds < 0:
        age_seconds = 0.0

    if age_seconds > max_age_seconds:
        return (
            False,
            "metrics file is stale: "
            f"last updated {age_seconds:.2f} seconds ago, "
            f"exceeding {max_age_seconds} seconds",
        )

    return True, f"processing-agent metrics are healthy: updated {age_seconds:.2f} seconds ago"


def main() -> int:
    healthy, message = check_metrics_snapshot(
        path=_metrics_file_path(),
        max_age_seconds=_max_age_seconds(),
    )
    print(message, flush=True)
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())

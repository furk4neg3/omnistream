import json
from datetime import datetime, timezone
from pathlib import Path

from app.models import DependencyStatus


def _parse_updated_at(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def load_dependency_status(path: str, max_age_seconds: int) -> DependencyStatus:
    status_path = Path(path)

    if not status_path.exists():
        return DependencyStatus(
            available=False,
            path=str(status_path),
            reason="metrics file not found",
        )

    if not status_path.is_file():
        return DependencyStatus(
            available=False,
            path=str(status_path),
            reason="metrics path is not a file",
        )

    try:
        with status_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as e:
        return DependencyStatus(
            available=False,
            path=str(status_path),
            reason=f"metrics file contains invalid JSON: {e.msg}",
        )
    except OSError as e:
        return DependencyStatus(
            available=False,
            path=str(status_path),
            reason=f"metrics file is unreadable: {e.strerror or type(e).__name__}",
        )

    if not isinstance(payload, dict):
        return DependencyStatus(
            available=False,
            path=str(status_path),
            reason="metrics file must contain a JSON object",
        )

    updated_at = _parse_updated_at(payload.get("updated_at"))
    age_seconds = None
    fresh = None
    if updated_at is not None:
        age_seconds = round(
            max(0.0, (datetime.now(timezone.utc) - updated_at).total_seconds()),
            2,
        )

        if payload.get("status") == "running":
            fresh = age_seconds <= max_age_seconds

            if not fresh:
                return DependencyStatus(
                    available=False,
                    path=str(status_path),
                    reason=(
                        "metrics file is stale: "
                        f"last updated {age_seconds} seconds ago, "
                        f"exceeding {max_age_seconds} seconds"
                    ),
                    fresh=False,
                    age_seconds=age_seconds,
                    payload=payload,
                )

    return DependencyStatus(
        available=True,
        path=str(status_path),
        fresh=fresh,
        age_seconds=age_seconds,
        payload=payload,
    )

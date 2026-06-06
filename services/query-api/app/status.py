import json
from pathlib import Path

from app.models import DependencyStatus


def load_dependency_status(path: str) -> DependencyStatus:
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

    return DependencyStatus(
        available=True,
        path=str(status_path),
        payload=payload,
    )

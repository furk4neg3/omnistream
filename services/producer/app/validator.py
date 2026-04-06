import json
from pathlib import Path

from jsonschema import validate


def load_raw_event_schema() -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "schemas" / "raw_event.json"

    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


RAW_EVENT_SCHEMA = load_raw_event_schema()


def validate_event(event: dict) -> None:
    validate(instance=event, schema=RAW_EVENT_SCHEMA)
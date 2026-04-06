import json
from pathlib import Path

from jsonschema import validate


def load_schema(schema_name: str) -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "schemas" / schema_name

    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


RAW_EVENT_SCHEMA = load_schema("raw_event.json")
ENRICHED_EVENT_SCHEMA = load_schema("enriched_event.json")


def validate_raw_event(event: dict) -> None:
    validate(instance=event, schema=RAW_EVENT_SCHEMA)


def validate_enriched_event(event: dict) -> None:
    validate(instance=event, schema=ENRICHED_EVENT_SCHEMA)
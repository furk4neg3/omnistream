import json
from pathlib import Path


def read_new_jsonl_records(input_file: str, start_line: int, max_records: int) -> tuple[list[dict], int]:
    path = Path(input_file)

    if not path.exists():
        return [], start_line

    records: list[dict] = []
    next_line = start_line

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f):
            if line_number < start_line:
                continue

            stripped = line.strip()
            next_line = line_number + 1

            if not stripped:
                continue

            records.append(json.loads(stripped))
            if len(records) >= max_records:
                break

    return records, next_line
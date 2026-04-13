import json
from pathlib import Path


def append_jsonl(output_file: str, records: list[dict]) -> None:
    if not records:
        return

    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
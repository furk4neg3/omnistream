import json
from pathlib import Path


def write_jsonl(output_file: str, records) -> None:
    path = Path(output_file)

    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
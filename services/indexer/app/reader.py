import json
from pathlib import Path


def read_jsonl(input_file: str):
    path = Path(input_file)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
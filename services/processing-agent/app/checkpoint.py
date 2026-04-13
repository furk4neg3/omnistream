import json
from pathlib import Path


def load_checkpoint(checkpoint_file: str) -> dict:
    path = Path(checkpoint_file)
    if not path.exists():
        return {"lines_processed": 0}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(checkpoint_file: str, lines_processed: int) -> None:
    path = Path(checkpoint_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump({"lines_processed": lines_processed}, f, ensure_ascii=False, indent=2)
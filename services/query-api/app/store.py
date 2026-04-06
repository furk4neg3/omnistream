import json
from pathlib import Path
from typing import Any

import numpy as np


def load_local_vector_store(vector_store_dir: str) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    store_path = Path(vector_store_dir)

    embeddings = np.load(store_path / "embeddings.npy")

    records: list[dict[str, Any]] = []
    with (store_path / "records.jsonl").open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    with (store_path / "manifest.json").open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    return embeddings, records, manifest
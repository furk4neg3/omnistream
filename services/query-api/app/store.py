import json
from pathlib import Path
from typing import Any

import numpy as np


EMPTY_EMBEDDINGS = np.empty((0, 0), dtype="float32")


def _empty_manifest() -> dict[str, Any]:
    return {
        "model_name": "",
        "record_count": 0,
        "embedding_dim": 0,
    }


def get_store_version(vector_store_dir: str) -> float:
    manifest_path = Path(vector_store_dir) / "manifest.json"
    if not manifest_path.exists():
        return 0.0
    return manifest_path.stat().st_mtime


def load_local_vector_store(vector_store_dir: str) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    store_path = Path(vector_store_dir)
    embeddings_path = store_path / "embeddings.npy"
    records_path = store_path / "records.jsonl"
    manifest_path = store_path / "manifest.json"

    if not embeddings_path.exists() or not records_path.exists() or not manifest_path.exists():
        return EMPTY_EMBEDDINGS, [], _empty_manifest()

    embeddings = np.load(embeddings_path)

    records: list[dict[str, Any]] = []
    with records_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    return embeddings, records, manifest
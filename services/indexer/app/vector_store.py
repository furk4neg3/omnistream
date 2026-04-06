import json
from pathlib import Path
from typing import Any

import numpy as np


def write_local_vector_store(
    vector_store_dir: str,
    embeddings: np.ndarray,
    records: list[dict[str, Any]],
    model_name: str,
) -> None:
    store_path = Path(vector_store_dir)
    store_path.mkdir(parents=True, exist_ok=True)

    np.save(store_path / "embeddings.npy", embeddings)

    with (store_path / "records.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    manifest = {
        "model_name": model_name,
        "record_count": len(records),
        "embedding_dim": int(embeddings.shape[1]) if embeddings.size else 0,
    }

    with (store_path / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def load_local_vector_store(vector_store_dir: str) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    store_path = Path(vector_store_dir)

    embeddings = np.load(store_path / "embeddings.npy")

    records = []
    with (store_path / "records.jsonl").open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    with (store_path / "manifest.json").open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    return embeddings, records, manifest


def search_local_vector_store(
    embeddings: np.ndarray,
    records: list[dict[str, Any]],
    query_embedding: np.ndarray,
    top_k: int = 5,
    tenant_id: str | None = None,
) -> list[dict[str, Any]]:
    if embeddings.size == 0 or not records:
        return []

    scores = embeddings @ query_embedding.reshape(-1)

    indexed = []
    for i, score in enumerate(scores):
        record = records[i]

        if tenant_id and record["metadata"]["tenant_id"] != tenant_id:
            continue

        indexed.append(
            {
                "score": float(score),
                **record,
            }
        )

    indexed.sort(key=lambda x: x["score"], reverse=True)
    return indexed[:top_k]
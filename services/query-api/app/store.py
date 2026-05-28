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


def write_local_vector_store(
    vector_store_dir: str,
    embeddings: np.ndarray,
    records: list[dict[str, Any]],
    model_name: str,
) -> dict[str, Any]:
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

    return manifest


def upsert_local_vector_store(
    vector_store_dir: str,
    embeddings: np.ndarray,
    records: list[dict[str, Any]],
    model_name: str,
) -> dict[str, Any]:
    existing_embeddings, existing_records, existing_manifest = load_local_vector_store(vector_store_dir)

    stored_model_name = existing_manifest.get("model_name") or ""
    if existing_records and stored_model_name and stored_model_name != model_name:
        raise ValueError(
            f"Vector store was created with embedding model '{stored_model_name}', but query-api is using '{model_name}'."
        )

    incoming_chunk_ids = {record["chunk_id"] for record in records}

    kept_records: list[dict[str, Any]] = []
    kept_indices: list[int] = []
    for idx, record in enumerate(existing_records):
        if record["chunk_id"] in incoming_chunk_ids:
            continue
        kept_records.append(record)
        kept_indices.append(idx)

    if existing_embeddings.size == 0 or not kept_indices:
        kept_embeddings = EMPTY_EMBEDDINGS
    else:
        kept_embeddings = existing_embeddings[kept_indices]

    if kept_embeddings.size and embeddings.size and kept_embeddings.shape[1] != embeddings.shape[1]:
        raise ValueError("Embedding dimension mismatch while updating local vector store.")

    if kept_embeddings.size == 0 and embeddings.size == 0:
        combined_embeddings = EMPTY_EMBEDDINGS
    elif kept_embeddings.size == 0:
        combined_embeddings = embeddings
    elif embeddings.size == 0:
        combined_embeddings = kept_embeddings
    else:
        combined_embeddings = np.vstack([kept_embeddings, embeddings]).astype("float32")

    combined_records = kept_records + records

    return write_local_vector_store(
        vector_store_dir=vector_store_dir,
        embeddings=combined_embeddings,
        records=combined_records,
        model_name=model_name,
    )

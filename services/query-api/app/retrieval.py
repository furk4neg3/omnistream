from datetime import datetime
from typing import Any

import numpy as np

from app.embedder import LocalEmbedder
from app.models import Filters
from app.store import get_store_version, load_local_vector_store, upsert_local_vector_store


def parse_timestamp(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def record_matches_filters(record: dict[str, Any], tenant_id: str, filters: Filters | None) -> bool:
    metadata = record["metadata"]

    if metadata["tenant_id"] != tenant_id:
        return False

    if not filters:
        return True

    if filters.severity and metadata["severity"] not in filters.severity:
        return False

    if filters.product and metadata["product"] not in filters.product:
        return False

    if filters.customer_tier and metadata["customer_tier"] not in filters.customer_tier:
        return False

    record_time = parse_timestamp(metadata["timestamp"])

    if filters.start_time and record_time < filters.start_time:
        return False

    if filters.end_time and record_time > filters.end_time:
        return False

    return True


class QueryEngine:
    def __init__(self, vector_store_dir: str, embedding_model_name: str) -> None:
        self.vector_store_dir = vector_store_dir
        self.embedding_model_name = embedding_model_name
        self.embedder = LocalEmbedder(embedding_model_name)
        self.embeddings = np.empty((0, 0), dtype="float32")
        self.records: list[dict[str, Any]] = []
        self.manifest: dict[str, Any] = {}
        self._store_version = 0.0
        self.reload()

    def reload(self) -> None:
        embeddings, records, manifest = load_local_vector_store(self.vector_store_dir)

        stored_model_name = manifest.get("model_name") or ""
        if records and stored_model_name and stored_model_name != self.embedding_model_name:
            raise RuntimeError(
                f"Vector store model mismatch: store='{stored_model_name}', query-api='{self.embedding_model_name}'."
            )

        if not stored_model_name:
            manifest["model_name"] = self.embedding_model_name

        self.embeddings = embeddings
        self.records = records
        self.manifest = manifest
        self._store_version = get_store_version(self.vector_store_dir)

    def reload_if_changed(self) -> None:
        current_version = get_store_version(self.vector_store_dir)
        if current_version > self._store_version:
            self.reload()

    def search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        filters: Filters | None = None,
    ) -> list[dict[str, Any]]:
        self.reload_if_changed()

        if not self.records or self.embeddings.size == 0:
            return []

        query_embedding = self.embedder.encode([query])[0]
        scores = self.embeddings @ query_embedding.reshape(-1)

        candidates: list[dict[str, Any]] = []
        for i, score in enumerate(scores):
            record = self.records[i]
            if not record_matches_filters(record, tenant_id, filters):
                continue

            candidates.append(
                {
                    "chunk_id": record["chunk_id"],
                    "ticket_id": record["ticket_id"],
                    "score": float(score),
                    "text": record["text"],
                    "metadata": record["metadata"],
                }
            )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    def ingest_chunk_records(self, chunk_records: list[dict[str, Any]]) -> dict[str, Any]:
        chunk_texts = [record["text"] for record in chunk_records]
        embeddings = self.embedder.encode(chunk_texts)
        manifest = upsert_local_vector_store(
            vector_store_dir=self.vector_store_dir,
            embeddings=embeddings,
            records=chunk_records,
            model_name=self.embedding_model_name,
        )
        self.reload()
        return manifest

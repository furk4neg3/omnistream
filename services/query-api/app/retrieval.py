from datetime import datetime
from typing import Any

import numpy as np

from app.embedder import LocalEmbedder
from app.models import Filters
from app.store import load_local_vector_store


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
        self.embeddings, self.records, self.manifest = load_local_vector_store(vector_store_dir)
        self.embedder = LocalEmbedder(embedding_model_name)

    def search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        filters: Filters | None = None,
    ) -> list[dict[str, Any]]:
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
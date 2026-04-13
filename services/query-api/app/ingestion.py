from datetime import datetime, timezone
from typing import Any

from app.config import Settings
from app.models import RawEvent


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(title: str, body: str) -> str:
    combined = f"{title.strip()}\n\n{body.strip()}"
    return " ".join(combined.split())


def chunk_text(text: str, chunk_size_words: int, chunk_overlap_words: int) -> list[dict[str, Any]]:
    words = text.split()

    if not words:
        return []

    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be greater than 0")

    if chunk_overlap_words < 0:
        raise ValueError("chunk_overlap_words cannot be negative")

    if chunk_overlap_words >= chunk_size_words:
        raise ValueError("chunk_overlap_words must be smaller than chunk_size_words")

    chunks: list[dict[str, Any]] = []
    start = 0
    chunk_index = 0
    step = chunk_size_words - chunk_overlap_words

    while start < len(words):
        end = start + chunk_size_words
        chunk_words = words[start:end]

        chunks.append(
            {
                "chunk_index": chunk_index,
                "text": " ".join(chunk_words),
                "token_count": len(chunk_words),
            }
        )

        chunk_index += 1
        start += step

    return chunks


def transform_raw_to_enriched(raw_event: RawEvent, settings: Settings) -> dict[str, Any]:
    payload = raw_event.payload
    clean_text = normalize_text(
        title=payload.title,
        body=payload.body,
    )

    raw_chunks = chunk_text(
        text=clean_text,
        chunk_size_words=settings.chunk_size_words,
        chunk_overlap_words=settings.chunk_overlap_words,
    )

    chunks: list[dict[str, Any]] = []
    for chunk in raw_chunks:
        chunk_id = f"{payload.ticket_id}_chunk_{chunk['chunk_index']}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "token_count": chunk["token_count"],
            }
        )

    return {
        "event_id": raw_event.event_id,
        "ticket_id": payload.ticket_id,
        "tenant_id": raw_event.tenant_id,
        "timestamp": raw_event.timestamp.isoformat(),
        "source": raw_event.source,
        "severity": payload.severity,
        "product": payload.product,
        "customer_tier": payload.customer_tier,
        "language": payload.language,
        "clean_text": clean_text,
        "chunks": chunks,
        "metadata": {
            "ingested_at": utc_now_iso(),
            "schema_version": settings.schema_version,
            "processing_version": settings.processing_version,
            "router_label": raw_event.source,
            "summary": payload.title,
            "entities": payload.tags,
        },
    }


def build_chunk_records(enriched_event: dict[str, Any]) -> list[dict[str, Any]]:
    chunk_records: list[dict[str, Any]] = []

    for chunk in enriched_event["chunks"]:
        chunk_records.append(
            {
                "chunk_id": chunk["chunk_id"],
                "ticket_id": enriched_event["ticket_id"],
                "text": chunk["text"],
                "metadata": {
                    "tenant_id": enriched_event["tenant_id"],
                    "severity": enriched_event["severity"],
                    "product": enriched_event["product"],
                    "timestamp": enriched_event["timestamp"],
                    "customer_tier": enriched_event["customer_tier"],
                    "source": enriched_event["source"],
                },
            }
        )

    return chunk_records
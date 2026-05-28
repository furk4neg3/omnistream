from datetime import datetime, timezone
from typing import Any

from app.chunker import chunk_text
from app.router import ROUTE_VERSION, RoutedEvent, route_raw_event


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(title: str, body: str) -> str:
    combined = f"{title.strip()}\n\n{body.strip()}"
    return " ".join(combined.split())


def transform_raw_to_enriched(
    raw_event: dict,
    chunk_size_words: int,
    chunk_overlap_words: int,
    schema_version: str,
    processing_version: str,
) -> dict:
    route = route_raw_event(raw_event)
    return enrich_routed_event(
        raw_event=raw_event,
        route=route,
        chunk_size_words=chunk_size_words,
        chunk_overlap_words=chunk_overlap_words,
        schema_version=schema_version,
        processing_version=processing_version,
    )


def enrich_routed_event(
    raw_event: dict[str, Any],
    route: RoutedEvent,
    chunk_size_words: int,
    chunk_overlap_words: int,
    schema_version: str,
    processing_version: str,
) -> dict[str, Any]:

    clean_text = normalize_text(
        title=route.title,
        body=route.body,
    )

    raw_chunks = chunk_text(
        text=clean_text,
        chunk_size_words=chunk_size_words,
        chunk_overlap_words=chunk_overlap_words,
    )

    chunks = []
    for chunk in raw_chunks:
        chunk_id = f"{route.chunk_id_prefix}_chunk_{chunk['chunk_index']}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "token_count": chunk["token_count"],
            }
        )

    return {
        "event_id": raw_event["event_id"],
        "ticket_id": route.record_id,
        "tenant_id": raw_event["tenant_id"],
        "timestamp": raw_event["timestamp"],
        "source": raw_event["source"],
        "severity": route.severity,
        "product": route.product,
        "customer_tier": route.customer_tier,
        "language": route.language,
        "clean_text": clean_text,
        "chunks": chunks,
        "metadata": {
            "ingested_at": utc_now_iso(),
            "schema_version": schema_version,
            "processing_version": processing_version,
            "router_label": route.router_label,
            "event_type": route.event_type,
            "record_id": route.record_id,
            "source_payload_id": route.source_payload_id,
            "route_version": ROUTE_VERSION,
            "summary": route.summary,
            "entities": route.entities,
        },
    }


def build_chunk_records(enriched_event: dict) -> list[dict]:
    chunk_records = []

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
                    "event_type": enriched_event["metadata"].get("event_type"),
                    "record_id": enriched_event["metadata"].get("record_id"),
                    "source_payload_id": enriched_event["metadata"].get("source_payload_id"),
                    "router_label": enriched_event["metadata"].get("router_label"),
                },
            }
        )

    return chunk_records

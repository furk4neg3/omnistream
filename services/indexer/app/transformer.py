from datetime import datetime, timezone

from app.chunker import chunk_text


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
    payload = raw_event["payload"]

    clean_text = normalize_text(
        title=payload["title"],
        body=payload["body"],
    )

    raw_chunks = chunk_text(
        text=clean_text,
        chunk_size_words=chunk_size_words,
        chunk_overlap_words=chunk_overlap_words,
    )

    chunks = []
    for chunk in raw_chunks:
        chunk_id = f'{payload["ticket_id"]}_chunk_{chunk["chunk_index"]}'
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
        "ticket_id": payload["ticket_id"],
        "tenant_id": raw_event["tenant_id"],
        "timestamp": raw_event["timestamp"],
        "source": raw_event["source"],
        "severity": payload["severity"],
        "product": payload["product"],
        "customer_tier": payload["customer_tier"],
        "language": payload.get("language", "en"),
        "clean_text": clean_text,
        "chunks": chunks,
        "metadata": {
            "ingested_at": utc_now_iso(),
            "schema_version": schema_version,
            "processing_version": processing_version,
            "router_label": "support_ticket",
            "summary": payload["title"],
            "entities": payload.get("tags", []),
        },
    }
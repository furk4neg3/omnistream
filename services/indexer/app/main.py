from app.config import Settings
from app.embedder import LocalEmbedder
from app.reader import read_jsonl
from app.transformer import transform_raw_to_enriched
from app.validator import validate_enriched_event, validate_raw_event
from app.vector_store import write_local_vector_store
from app.writer import write_jsonl


def main() -> None:
    settings = Settings()
    enriched_records = []

    print(
        f"Starting indexer: input={settings.input_file}, "
        f"output={settings.output_file}, "
        f"vector_store={settings.vector_store_dir}"
    )

    count = 0
    for raw_event in read_jsonl(settings.input_file):
        validate_raw_event(raw_event)

        enriched_event = transform_raw_to_enriched(
            raw_event=raw_event,
            chunk_size_words=settings.chunk_size_words,
            chunk_overlap_words=settings.chunk_overlap_words,
            schema_version=settings.schema_version,
            processing_version=settings.processing_version,
        )

        validate_enriched_event(enriched_event)
        enriched_records.append(enriched_event)
        count += 1

    write_jsonl(settings.output_file, enriched_records)

    chunk_records = []
    chunk_texts = []

    for enriched_event in enriched_records:
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
            chunk_texts.append(chunk["text"])

    embedder = LocalEmbedder(settings.embedding_model_name)
    embeddings = embedder.encode(chunk_texts)

    write_local_vector_store(
        vector_store_dir=settings.vector_store_dir,
        embeddings=embeddings,
        records=chunk_records,
        model_name=settings.embedding_model_name,
    )

    print(
        f"Indexer finished. Processed {count} events and stored "
        f"{len(chunk_records)} chunk vectors."
    )


if __name__ == "__main__":
    main()
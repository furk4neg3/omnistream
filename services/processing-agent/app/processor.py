from app.checkpoint import load_checkpoint, save_checkpoint
from app.config import Settings
from app.embedder import LocalEmbedder
from app.reader import read_new_jsonl_records
from app.router import route_raw_event
from app.transformer import build_chunk_records, enrich_routed_event
from app.validator import validate_enriched_event, validate_raw_event
from app.vector_store import upsert_local_vector_store
from app.writer import append_jsonl


class ProcessingAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedder = None

    def _get_embedder(self):
        if self.embedder is None:
            self.embedder = LocalEmbedder(self.settings.embedding_model_name)
        return self.embedder

    def process_once(self) -> dict:
        checkpoint = load_checkpoint(self.settings.checkpoint_file)
        start_line = int(checkpoint.get("lines_processed", 0))

        raw_events, next_line = read_new_jsonl_records(
            input_file=self.settings.input_file,
            start_line=start_line,
            max_records=self.settings.batch_size,
        )

        if not raw_events:
            return {
                "raw_events_processed": 0,
                "chunks_written": 0,
                "vector_record_count": None,
                "next_line": start_line,
            }

        enriched_events = []
        chunk_records = []
        chunk_texts = []

        for raw_event in raw_events:
            validate_raw_event(raw_event)
            route = route_raw_event(raw_event)

            enriched_event = enrich_routed_event(
                raw_event=raw_event,
                route=route,
                chunk_size_words=self.settings.chunk_size_words,
                chunk_overlap_words=self.settings.chunk_overlap_words,
                schema_version=self.settings.schema_version,
                processing_version=self.settings.processing_version,
            )

            validate_enriched_event(enriched_event)
            enriched_events.append(enriched_event)

            event_chunk_records = build_chunk_records(enriched_event)
            chunk_records.extend(event_chunk_records)
            chunk_texts.extend(record["text"] for record in event_chunk_records)

        append_jsonl(self.settings.output_file, enriched_events)

        embeddings = self._get_embedder().encode(chunk_texts)
        manifest = upsert_local_vector_store(
            vector_store_dir=self.settings.vector_store_dir,
            embeddings=embeddings,
            records=chunk_records,
            model_name=self.settings.embedding_model_name,
        )

        save_checkpoint(self.settings.checkpoint_file, next_line)

        return {
            "raw_events_processed": len(raw_events),
            "chunks_written": len(chunk_records),
            "vector_record_count": manifest["record_count"],
            "next_line": next_line,
        }

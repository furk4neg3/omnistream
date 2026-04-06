import os
from dataclasses import dataclass


@dataclass
class Settings:
    input_file: str = os.getenv("INPUT_FILE", "../producer/events.jsonl")
    output_file: str = os.getenv("OUTPUT_FILE", "enriched_events.jsonl")
    vector_store_dir: str = os.getenv("VECTOR_STORE_DIR", "local_vector_store")
    chunk_size_words: int = int(os.getenv("CHUNK_SIZE_WORDS", "80"))
    chunk_overlap_words: int = int(os.getenv("CHUNK_OVERLAP_WORDS", "20"))
    schema_version: str = os.getenv("SCHEMA_VERSION", "v1")
    processing_version: str = os.getenv("PROCESSING_VERSION", "v1")
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
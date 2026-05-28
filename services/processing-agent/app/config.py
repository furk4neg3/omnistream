import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass
class Settings:
    input_file: str = os.getenv(
        "INPUT_FILE",
        str(REPO_ROOT / "services" / "producer" / "events.jsonl"),
    )
    output_file: str = os.getenv(
        "OUTPUT_FILE",
        str(SERVICE_ROOT / "enriched_events.jsonl"),
    )
    checkpoint_file: str = os.getenv(
        "CHECKPOINT_FILE",
        str(SERVICE_ROOT / "state" / "checkpoint.json"),
    )
    metrics_file: str = os.getenv(
        "METRICS_FILE",
        str(SERVICE_ROOT / "state" / "metrics.json"),
    )
    vector_store_dir: str = os.getenv(
        "VECTOR_STORE_DIR",
        str(REPO_ROOT / "services" / "indexer" / "local_vector_store"),
    )
    poll_interval_seconds: float = float(os.getenv("POLL_INTERVAL_SECONDS", "1.0"))
    loop_forever: bool = os.getenv("LOOP_FOREVER", "true").lower() in {"1", "true", "yes", "on"}
    batch_size: int = int(os.getenv("BATCH_SIZE", "32"))
    chunk_size_words: int = int(os.getenv("CHUNK_SIZE_WORDS", "80"))
    chunk_overlap_words: int = int(os.getenv("CHUNK_OVERLAP_WORDS", "20"))
    schema_version: str = os.getenv("SCHEMA_VERSION", "v1")
    processing_version: str = os.getenv("PROCESSING_VERSION", "v1")
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

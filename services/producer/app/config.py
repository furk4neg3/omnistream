import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass
class Settings:
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    output_mode: str = os.getenv("OUTPUT_MODE", "file")  # stdout | file | kinesis
    kinesis_stream_name: str = os.getenv("KINESIS_STREAM_NAME", "omnistream-raw-events")
    tenant_id: str = os.getenv("TENANT_ID", "acme")
    events_per_second: float = float(os.getenv("EVENTS_PER_SECOND", "1"))
    max_events: int = int(os.getenv("MAX_EVENTS", "10"))
    output_file: str = os.getenv(
        "OUTPUT_FILE",
        str(SERVICE_ROOT / "events.jsonl"),
    )
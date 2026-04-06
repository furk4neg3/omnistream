import os
from dataclasses import dataclass


@dataclass
class Settings:
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    output_mode: str = os.getenv("OUTPUT_MODE", "stdout")  # stdout | file | kinesis
    kinesis_stream_name: str = os.getenv("KINESIS_STREAM_NAME", "omnistream-raw-events")
    tenant_id: str = os.getenv("TENANT_ID", "acme")
    events_per_second: float = float(os.getenv("EVENTS_PER_SECOND", "1"))
    max_events: int = int(os.getenv("MAX_EVENTS", "10"))
    output_file: str = os.getenv("OUTPUT_FILE", "producer_output.jsonl")
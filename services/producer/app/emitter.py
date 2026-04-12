import json
from pathlib import Path


class EventEmitter:
    def emit(self, event: dict) -> None:
        raise NotImplementedError


class StdoutEmitter(EventEmitter):
    def emit(self, event: dict) -> None:
        print(json.dumps(event, ensure_ascii=False))


class FileEmitter(EventEmitter):
    def __init__(self, output_file: str) -> None:
        self.output_path = Path(output_file)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: dict) -> None:
        with self.output_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


class KinesisEmitter(EventEmitter):
    def __init__(self, stream_name: str, aws_region: str) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError(
                "KinesisEmitter requires boto3. Install it with "
                "'pip install boto3' or use OUTPUT_MODE=file/stdout."
            ) from exc

        self.stream_name = stream_name
        self.client = boto3.client("kinesis", region_name=aws_region)

    def emit(self, event: dict) -> None:
        self.client.put_record(
            StreamName=self.stream_name,
            Data=json.dumps(event).encode("utf-8"),
            PartitionKey=event["tenant_id"],
        )
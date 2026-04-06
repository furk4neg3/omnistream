import time

from app.config import Settings
from app.emitter import FileEmitter, KinesisEmitter, StdoutEmitter
from app.generator import generate_event
from app.validator import validate_event


def get_emitter(settings: Settings):
    if settings.output_mode == "stdout":
        return StdoutEmitter()
    if settings.output_mode == "file":
        return FileEmitter(settings.output_file)
    if settings.output_mode == "kinesis":
        return KinesisEmitter(
            stream_name=settings.kinesis_stream_name,
            aws_region=settings.aws_region,
        )
    raise ValueError(f"Unsupported OUTPUT_MODE: {settings.output_mode}")


def main() -> None:
    settings = Settings()
    emitter = get_emitter(settings)
    delay = 1 / settings.events_per_second if settings.events_per_second > 0 else 0

    print(
        f"Starting producer: mode={settings.output_mode}, "
        f"tenant={settings.tenant_id}, max_events={settings.max_events}"
    )

    for _ in range(settings.max_events):
        event = generate_event(settings.tenant_id)
        validate_event(event)
        emitter.emit(event)
        if delay > 0:
            time.sleep(delay)

    print("Producer finished.")


if __name__ == "__main__":
    main()
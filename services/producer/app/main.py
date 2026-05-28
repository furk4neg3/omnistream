import time

from app.config import Settings
from app.emitter import FileEmitter, KinesisEmitter, StdoutEmitter
from app.generator import generate_event
from app.observability import ProducerMetrics, log_event, write_status_file
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
    metrics = ProducerMetrics(settings)
    delay = 1 / settings.events_per_second if settings.events_per_second > 0 else 0

    log_event(
        "producer_started",
        output_mode=settings.output_mode,
        tenant_id=settings.tenant_id,
        max_events=settings.max_events,
        event_types=settings.enabled_event_types,
        events_per_second=settings.events_per_second,
        output_file=settings.output_file if settings.output_mode == "file" else None,
        metrics_file=settings.metrics_file,
    )
    write_status_file(settings.metrics_file, metrics.snapshot(status="running"))

    try:
        for _ in range(settings.max_events):
            event = generate_event(
                tenant_id=settings.tenant_id,
                event_types=settings.enabled_event_types,
            )
            validate_event(event)
            emitter.emit(event)
            metrics.record_event(event)
            payload = event["payload"]
            record_id = payload.get("ticket_id") or payload.get("conversation_id")
            source_payload_id = payload.get("message_id") or payload.get("ticket_id")
            write_status_file(settings.metrics_file, metrics.snapshot(status="running"))
            log_event(
                "event_emitted",
                event_id=event["event_id"],
                source=event["source"],
                record_id=record_id,
                source_payload_id=source_payload_id,
                tenant_id=event["tenant_id"],
                events_emitted_total=metrics.counters["events_emitted_total"],
            )
            if delay > 0:
                time.sleep(delay)
    except Exception as e:
        metrics.record_error(e)
        write_status_file(settings.metrics_file, metrics.snapshot(status="error"))
        log_event(
            "producer_failed",
            level="error",
            error_type=type(e).__name__,
            error=str(e),
            events_emitted_total=metrics.counters["events_emitted_total"],
        )
        raise

    write_status_file(settings.metrics_file, metrics.snapshot(status="completed"))
    log_event(
        "producer_completed",
        events_emitted_total=metrics.counters["events_emitted_total"],
    )


if __name__ == "__main__":
    main()

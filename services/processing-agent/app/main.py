import time
from time import perf_counter

from app.config import Settings
from app.observability import AgentMetrics, log_event, write_status_file
from app.processor import ProcessingAgent


def main() -> None:
    settings = Settings()
    agent = ProcessingAgent(settings)
    metrics = AgentMetrics(settings)

    log_event(
        "processing_agent_started",
        input_file=settings.input_file,
        output_file=settings.output_file,
        vector_store_dir=settings.vector_store_dir,
        checkpoint_file=settings.checkpoint_file,
        metrics_file=settings.metrics_file,
        loop_forever=settings.loop_forever,
        poll_interval_seconds=settings.poll_interval_seconds,
    )
    write_status_file(settings.metrics_file, metrics.snapshot())

    idle_streak = 0

    while True:
        start = perf_counter()
        try:
            result = agent.process_once()
        except Exception as e:
            processing_ms = (perf_counter() - start) * 1000
            metrics.record_error(e)
            write_status_file(settings.metrics_file, metrics.snapshot())
            log_event(
                "processing_batch_failed",
                level="error",
                error_type=type(e).__name__,
                error=str(e),
                processing_ms=round(processing_ms, 2),
            )
            raise

        processing_ms = (perf_counter() - start) * 1000
        metrics.record_result(result, processing_ms)
        write_status_file(settings.metrics_file, metrics.snapshot())

        if result["raw_events_processed"] > 0:
            idle_streak = 0
            log_event(
                "processing_batch_completed",
                raw_events_processed=result["raw_events_processed"],
                chunks_written=result["chunks_written"],
                vector_record_count=result["vector_record_count"],
                next_line=result["next_line"],
                processing_ms=round(processing_ms, 2),
            )
        else:
            idle_streak += 1
            if idle_streak == 1 or idle_streak % 10 == 0:
                log_event(
                    "processing_idle",
                    idle_streak=idle_streak,
                    next_line=result["next_line"],
                    processing_ms=round(processing_ms, 2),
                )

        if not settings.loop_forever:
            break

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()

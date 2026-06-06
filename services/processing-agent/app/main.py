import signal
import threading
from time import perf_counter
from types import FrameType
from typing import Callable

from app.config import Settings
from app.observability import AgentMetrics, log_event, write_status_file
from app.processor import ProcessingAgent


class ShutdownController:
    def __init__(self, metrics: AgentMetrics, metrics_file: str) -> None:
        self.metrics = metrics
        self.metrics_file = metrics_file
        self.requested = False
        self.signal_name: str | None = None
        self._event = threading.Event()
        self._previous_handlers: dict[signal.Signals, Callable[..., object] | int | None] = {}

    def install(self) -> None:
        for handled_signal in (signal.SIGTERM, signal.SIGINT):
            self._previous_handlers[handled_signal] = signal.getsignal(handled_signal)
            signal.signal(handled_signal, self.request_shutdown)

    def restore(self) -> None:
        for handled_signal, previous_handler in self._previous_handlers.items():
            signal.signal(handled_signal, previous_handler)

    def request_shutdown(self, signum: int, _frame: FrameType | None) -> None:
        signal_name = _signal_name(signum)
        if self.requested:
            return

        self.requested = True
        self.signal_name = signal_name
        self.metrics.set_status("stopping")
        write_status_file(self.metrics_file, self.metrics.snapshot())
        log_event(
            "processing_shutdown_requested",
            signal_name=signal_name,
        )
        self._event.set()

    def wait(self, timeout: float) -> bool:
        return self._event.wait(timeout)


def _signal_name(signum: int) -> str | None:
    try:
        return signal.Signals(signum).name
    except ValueError:
        return None


def main() -> None:
    settings = Settings()
    agent = ProcessingAgent(settings)
    metrics = AgentMetrics(settings)
    shutdown = ShutdownController(metrics, settings.metrics_file)
    shutdown.install()

    try:
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
            if shutdown.requested:
                break

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
                    event_type_counts=result["event_type_counts"],
                    chunk_counts_by_event_type=result["chunk_counts_by_event_type"],
                    router_label_counts=result["router_label_counts"],
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

            if shutdown.requested or not settings.loop_forever:
                break

            if shutdown.wait(settings.poll_interval_seconds):
                break

        metrics.set_status("stopped")
        write_status_file(settings.metrics_file, metrics.snapshot())
    finally:
        shutdown.restore()


if __name__ == "__main__":
    main()

import time

from app.config import Settings
from app.processor import ProcessingAgent


def main() -> None:
    settings = Settings()
    agent = ProcessingAgent(settings)

    print(
        f"Starting processing-agent:\n"
        f"  input={settings.input_file}\n"
        f"  output={settings.output_file}\n"
        f"  vector_store={settings.vector_store_dir}\n"
        f"  checkpoint={settings.checkpoint_file}\n"
        f"  loop_forever={settings.loop_forever}\n"
        f"  poll_interval_seconds={settings.poll_interval_seconds}"
    )

    idle_streak = 0

    while True:
        result = agent.process_once()

        if result["raw_events_processed"] > 0:
            idle_streak = 0
            print(
                "Processed "
                f"{result['raw_events_processed']} raw events, "
                f"{result['chunks_written']} chunks, "
                f"vector_record_count={result['vector_record_count']}, "
                f"next_line={result['next_line']}"
            )
        else:
            idle_streak += 1
            if idle_streak == 1 or idle_streak % 10 == 0:
                print("No new events found.")

        if not settings.loop_forever:
            break

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
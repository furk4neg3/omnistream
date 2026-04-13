import time

from app.config import Settings
from app.processor import ProcessingAgent


def main() -> None:
    settings = Settings()
    agent = ProcessingAgent(settings)

    print(
        f"Starting processing-agent: input={settings.input_file}, output={settings.output_file}, "
        f"vector_store={settings.vector_store_dir}, loop_forever={settings.loop_forever}"
    )

    while True:
        result = agent.process_once()

        if result["raw_events_processed"] > 0:
            print(
                "Processed "
                f"{result['raw_events_processed']} raw events, "
                f"{result['chunks_written']} chunks, "
                f"vector_record_count={result['vector_record_count']}"
            )
        else:
            print("No new events found.")

        if not settings.loop_forever:
            break

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
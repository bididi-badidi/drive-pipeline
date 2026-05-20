"""
main.py — drive-pipeline entry point.

Starts the watchdog observer (watches originals/) and the worker loop
(polls SQLite queue, processes jobs) concurrently in a background thread.
"""

import logging
import signal
import sys
import threading

import config
from pipeline import queue, watcher, worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)


def main() -> None:
    config.ensure_dirs()
    queue.init_db()

    observer = watcher.start_observer()

    worker_thread = threading.Thread(target=worker.run_forever, daemon=True, name="worker")
    worker_thread.start()

    def _shutdown(sig, frame):  # noqa: ANN001
        logger.info("Shutting down (signal %s)…", sig)
        observer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("drive-pipeline running. Press Ctrl-C to stop.")
    observer.join()


if __name__ == "__main__":
    main()

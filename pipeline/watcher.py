"""
pipeline/watcher.py — watchdog observer for originals/.

Detects new files, detects their source type, enqueues them, then
moves them to processing/ so the worker can pick them up.
"""

import logging
import shutil
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

import config
from pipeline import queue

logger = logging.getLogger(__name__)


def _detect_type(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in config.DOCUMENT_EXTENSIONS:
        # .txt whose first line is a URL counts as a URL job
        if suffix == ".txt":
            try:
                first_line = path.read_text(errors="ignore").splitlines()[0].strip()
                if first_line.startswith(("http://", "https://")):
                    return "url"
            except (IndexError, OSError):
                pass
        return "url" if suffix == ".url" else "document"
    if suffix in config.IMAGE_EXTENSIONS:
        return "image"
    if suffix in config.URL_EXTENSIONS:
        return "url"
    if suffix in config.HTML_EXTENSIONS:
        return "html"
    return None


class _Handler(FileSystemEventHandler):
    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in config.ALL_SUPPORTED_EXTENSIONS:
            logger.debug("Ignoring unsupported file: %s", path.name)
            return

        source_type = _detect_type(path)
        dest = config.PROCESSING_DIR / path.name

        try:
            shutil.move(str(path), dest)
        except OSError as exc:
            logger.error("Could not move %s to processing/: %s", path.name, exc)
            return

        job_id = queue.enqueue(path.name, dest, source_type)
        logger.info("Enqueued job #%d  %s  (%s)", job_id, path.name, source_type)


def start_observer() -> Observer:
    """Start and return a running watchdog Observer. Call .stop() to halt."""
    config.ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(_Handler(), str(config.ORIGINALS_DIR), recursive=False)
    observer.start()
    logger.info("Watching %s", config.ORIGINALS_DIR)
    return observer

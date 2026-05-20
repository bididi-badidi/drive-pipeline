"""
pipeline/worker.py — polling worker loop.

Claims pending jobs from the SQLite queue, dispatches to the right
processor, then chunks → embeds → stores in ChromaDB.

On error: marks job failed, moves file to failed/, writes .error.txt.
"""

import logging
import shutil
import time
from pathlib import Path

import config
from pipeline import queue
from pipeline.chunker import chunk_text
from pipeline.embedder import embed_chunks
from pipeline.metadata import build_metadata
from pipeline.processors import document, image, url
from pipeline.vector_store import upsert_chunks

logger = logging.getLogger(__name__)

POLL_INTERVAL = 2  # seconds between queue polls


def _processor_for(source_type: str | None):
    dispatch = {
        "document": document.extract,
        "image": image.extract,
        "url": url.extract,
        "html": url.extract,  # reuses URL processor's HTML path
    }
    return dispatch.get(source_type or "")


def _handle_failure(job_id: int, file_path: Path, exc: Exception) -> None:
    error_msg = f"{type(exc).__name__}: {exc}"
    logger.error("Job #%d failed — %s", job_id, error_msg)
    queue.mark_failed(job_id, error_msg)

    dest = config.FAILED_DIR / file_path.name
    try:
        shutil.move(str(file_path), dest)
        dest.with_suffix(dest.suffix + ".error.txt").write_text(error_msg)
    except OSError as move_exc:
        logger.error("Could not move file to failed/: %s", move_exc)


def process_one(job: object) -> None:
    """Process a single claimed job row."""
    job_id: int = job["id"]
    filename: str = job["filename"]
    source_type: str | None = job["source_type"]
    file_path = Path(job["source_path"])

    logger.info("Processing job #%d  %s", job_id, filename)

    processor = _processor_for(source_type)
    if processor is None:
        raise ValueError(f"No processor for source_type={source_type!r}")

    text = processor(file_path)
    chunks = chunk_text(text)
    metadata_list = [
        build_metadata(
            job_id=job_id,
            filename=filename,
            source_path=file_path,
            source_type=source_type or "unknown",
            chunk_index=i,
            total_chunks=len(chunks),
        )
        for i in range(len(chunks))
    ]
    embeddings = embed_chunks(chunks)
    upsert_chunks(chunks, embeddings, metadata_list)

    queue.mark_done(job_id)
    # Clean up from processing/ after successful ingestion
    file_path.unlink(missing_ok=True)
    logger.info("Job #%d done", job_id)


def run_forever() -> None:
    """Block forever, polling the queue and processing jobs."""
    logger.info("Worker started (poll interval=%ds)", POLL_INTERVAL)
    while True:
        job = queue.claim_pending()
        if job is None:
            time.sleep(POLL_INTERVAL)
            continue
        file_path = Path(job["source_path"])
        try:
            process_one(job)
        except Exception as exc:  # noqa: BLE001
            _handle_failure(job["id"], file_path, exc)

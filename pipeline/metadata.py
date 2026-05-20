"""
pipeline/metadata.py — per-chunk metadata dict builder.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path


def build_metadata(
    *,
    job_id: int,
    filename: str,
    source_path: Path,
    source_type: str,
    chunk_index: int,
    total_chunks: int,
    tags: list[str] | None = None,
    drive_file_id: str | None = None,
    drive_web_view_link: str | None = None,
    drive_folder_id: str | None = None,
    drive_folder_path: str | None = None,
) -> dict:
    meta = {
        "chunk_id": str(uuid.uuid4()),
        "job_id": job_id,
        "filename": filename,
        "source_path": str(source_path),
        "source_type": source_type,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tags": tags or [],
    }
    if drive_file_id:
        meta["drive_file_id"] = drive_file_id
    if drive_web_view_link:
        meta["drive_web_view_link"] = drive_web_view_link
    if drive_folder_id:
        meta["drive_folder_id"] = drive_folder_id
    if drive_folder_path:
        meta["drive_folder_path"] = drive_folder_path
    return meta

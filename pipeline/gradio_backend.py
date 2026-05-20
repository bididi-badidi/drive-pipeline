"""
Backend helpers for the local Gradio operator console.

The UI imports this module rather than talking directly to Chroma, SQLite, or
the filesystem. That keeps the interface thin and the safety checks testable.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import config
from pipeline.embedder import embed_query
from pipeline.vector_store import delete_chunks, list_chunks, query


@dataclass(frozen=True)
class DeleteReport:
    source_path: str
    file_exists: bool
    file_deleted: bool
    chunks_matched: int
    chunks_deleted: int
    dry_run: bool
    message: str

    def as_rows(self) -> list[list[Any]]:
        return [
            ["source_path", self.source_path],
            ["file_exists", self.file_exists],
            ["file_deleted", self.file_deleted],
            ["chunks_matched", self.chunks_matched],
            ["chunks_deleted", self.chunks_deleted],
            ["dry_run", self.dry_run],
            ["message", self.message],
        ]


def list_drive_files() -> list[dict[str, Any]]:
    """List files under the configured local Drive working directories."""
    rows: list[dict[str, Any]] = []
    job_status = _latest_job_status()
    for root_name, root in (
        ("originals", config.ORIGINALS_DIR),
        ("processing", config.PROCESSING_DIR),
        ("failed", config.FAILED_DIR),
    ):
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            stat = path.stat()
            rows.append(
                {
                    "folder": root_name,
                    "filename": path.name,
                    "source_path": str(path),
                    "extension": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(
                        timespec="seconds"
                    ),
                    "job_status": job_status.get(str(path), ""),
                }
            )
    return rows


def list_vector_items(
    *,
    source_type: str = "",
    filename_contains: str = "",
    source_path_contains: str = "",
    limit: int = 100,
) -> list[dict[str, Any]]:
    where = _exact_where(source_type=source_type)
    rows = [_chunk_to_row(item) for item in list_chunks(where=where, limit=limit)]
    return _post_filter(rows, filename_contains, source_path_contains)


def search_vector_items(
    *,
    query_text: str,
    top_k: int = 10,
    source_type: str = "",
    filename_contains: str = "",
    source_path_contains: str = "",
    raw_where_json: str = "",
) -> list[dict[str, Any]]:
    if not query_text.strip():
        return []

    where = _exact_where(source_type=source_type)
    if raw_where_json.strip():
        where.update(json.loads(raw_where_json))

    results = query(embed_query(query_text), n_results=top_k, where=where or None)
    rows = [_chunk_to_row(item) for item in results]
    return _post_filter(rows, filename_contains, source_path_contains)


def preview_delete(source_path: str) -> DeleteReport:
    return delete_file_and_chunks(source_path, dry_run=True)


def delete_file_and_chunks(source_path: str, *, dry_run: bool) -> DeleteReport:
    path = _safe_source_path(source_path)
    chunks = list_chunks(where={"source_path": str(path)}, limit=10000)
    file_exists = path.exists()

    if dry_run:
        return DeleteReport(
            source_path=str(path),
            file_exists=file_exists,
            file_deleted=False,
            chunks_matched=len(chunks),
            chunks_deleted=0,
            dry_run=True,
            message="Dry run only. No file or chunks were deleted.",
        )

    file_deleted = False
    if file_exists:
        if path.is_dir():
            raise ValueError("Refusing to delete a directory")
        path.unlink()
        file_deleted = True

    chunks_deleted = delete_chunks({"source_path": str(path)})
    return DeleteReport(
        source_path=str(path),
        file_exists=file_exists,
        file_deleted=file_deleted,
        chunks_matched=len(chunks),
        chunks_deleted=chunks_deleted,
        dry_run=False,
        message="Deletion complete.",
    )


def list_gdrive_archive(limit: int = 200) -> list[dict[str, Any]]:
    """List files archived to Google Drive."""
    if not config.DRIVE_ARCHIVE_ENABLED:
        return []
    from pipeline import drive  # lazy — avoids loading Drive credentials at startup

    return drive.list_archived_files(limit=limit)


def _safe_source_path(source_path: str) -> Path:
    if not source_path.strip():
        raise ValueError("source_path is required")

    path = Path(source_path).expanduser().resolve(strict=False)
    allowed_roots = [
        config.ORIGINALS_DIR.resolve(strict=False),
        config.PROCESSING_DIR.resolve(strict=False),
        config.FAILED_DIR.resolve(strict=False),
    ]
    for root in allowed_roots:
        try:
            path.relative_to(root)
        except ValueError:
            continue
        return path
    raise ValueError("Refusing to delete outside the configured Drive working directories")


def _latest_job_status() -> dict[str, str]:
    if not config.SQLITE_DB_PATH.exists():
        return {}

    try:
        with sqlite3.connect(config.SQLITE_DB_PATH) as conn:
            rows = conn.execute(
                """
                SELECT source_path, status
                FROM jobs
                ORDER BY updated_at ASC, id ASC
                """
            ).fetchall()
    except sqlite3.Error:
        return {}

    return {source_path: status for source_path, status in rows}


def _exact_where(*, source_type: str = "") -> dict[str, Any]:
    where: dict[str, Any] = {}
    if source_type:
        where["source_type"] = source_type
    return where


def _chunk_to_row(item: dict[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata") or {}
    document = item.get("document") or ""
    return {
        "chunk_id": item.get("id", ""),
        "filename": metadata.get("filename", ""),
        "source_path": metadata.get("source_path", ""),
        "source_type": metadata.get("source_type", ""),
        "chunk_index": metadata.get("chunk_index", ""),
        "total_chunks": metadata.get("total_chunks", ""),
        "created_at": metadata.get("created_at", ""),
        "distance": item.get("distance", ""),
        "preview": document[:500],
        "metadata": json.dumps(metadata, indent=2, sort_keys=True),
    }


def _post_filter(
    rows: list[dict[str, Any]],
    filename_contains: str,
    source_path_contains: str,
) -> list[dict[str, Any]]:
    filename_filter = filename_contains.lower().strip()
    path_filter = source_path_contains.lower().strip()

    if filename_filter:
        rows = [row for row in rows if filename_filter in str(row["filename"]).lower()]
    if path_filter:
        rows = [row for row in rows if path_filter in str(row["source_path"]).lower()]
    return rows

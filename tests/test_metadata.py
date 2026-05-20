"""tests/test_metadata.py — unit tests for pipeline/metadata.py"""

import uuid
from pathlib import Path

from pipeline.metadata import build_metadata


def _base_kwargs(**overrides):
    defaults = dict(
        job_id=1,
        filename="test.pdf",
        source_path=Path("/some/path/test.pdf"),
        source_type="pdf",
        chunk_index=0,
        total_chunks=3,
    )
    defaults.update(overrides)
    return defaults


def test_required_keys_present():
    meta = build_metadata(**_base_kwargs())
    for key in (
        "chunk_id",
        "job_id",
        "filename",
        "source_path",
        "source_type",
        "chunk_index",
        "total_chunks",
        "created_at",
        "tags",
    ):
        assert key in meta, f"Missing key: {key}"


def test_chunk_id_is_valid_uuid():
    meta = build_metadata(**_base_kwargs())
    uuid.UUID(meta["chunk_id"])  # raises if invalid


def test_chunk_ids_are_unique():
    ids = {build_metadata(**_base_kwargs())["chunk_id"] for _ in range(10)}
    assert len(ids) == 10


def test_tags_defaults_to_empty_list():
    meta = build_metadata(**_base_kwargs())
    assert meta["tags"] == []


def test_tags_passed_through():
    meta = build_metadata(**_base_kwargs(tags=["important", "work"]))
    assert meta["tags"] == ["important", "work"]


def test_source_path_is_string():
    meta = build_metadata(**_base_kwargs())
    assert isinstance(meta["source_path"], str)


def test_values_match_inputs():
    meta = build_metadata(**_base_kwargs(job_id=42, chunk_index=2, total_chunks=5))
    assert meta["job_id"] == 42
    assert meta["chunk_index"] == 2
    assert meta["total_chunks"] == 5
    assert meta["filename"] == "test.pdf"
    assert meta["source_type"] == "pdf"


def test_drive_metadata_is_added_when_present():
    meta = build_metadata(
        **_base_kwargs(
            drive_file_id="drive-file",
            drive_web_view_link="https://drive/file",
            drive_folder_id="folder-id",
            drive_folder_path="archive/document/2026/05",
        )
    )

    assert meta["drive_file_id"] == "drive-file"
    assert meta["drive_web_view_link"] == "https://drive/file"
    assert meta["drive_folder_id"] == "folder-id"
    assert meta["drive_folder_path"] == "archive/document/2026/05"

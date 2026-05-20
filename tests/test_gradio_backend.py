from pathlib import Path

import pytest

from pipeline import gradio_backend


def test_safe_source_path_allows_configured_roots(tmp_path, monkeypatch):
    import config

    originals = tmp_path / "originals"
    processing = tmp_path / "processing"
    failed = tmp_path / "failed"
    for directory in (originals, processing, failed):
        directory.mkdir()

    monkeypatch.setattr(config, "ORIGINALS_DIR", originals)
    monkeypatch.setattr(config, "PROCESSING_DIR", processing)
    monkeypatch.setattr(config, "FAILED_DIR", failed)

    allowed = originals / "note.txt"
    assert gradio_backend._safe_source_path(str(allowed)) == allowed.resolve(strict=False)


def test_safe_source_path_rejects_outside_roots(tmp_path, monkeypatch):
    import config

    monkeypatch.setattr(config, "ORIGINALS_DIR", tmp_path / "originals")
    monkeypatch.setattr(config, "PROCESSING_DIR", tmp_path / "processing")
    monkeypatch.setattr(config, "FAILED_DIR", tmp_path / "failed")

    with pytest.raises(ValueError, match="outside"):
        gradio_backend._safe_source_path(str(Path("/tmp/not-drive-pipeline.txt")))


def test_preview_delete_is_dry_run(tmp_path, monkeypatch):
    import config

    originals = tmp_path / "originals"
    originals.mkdir()
    source = originals / "note.txt"
    source.write_text("hello")

    monkeypatch.setattr(config, "ORIGINALS_DIR", originals)
    monkeypatch.setattr(config, "PROCESSING_DIR", tmp_path / "processing")
    monkeypatch.setattr(config, "FAILED_DIR", tmp_path / "failed")
    monkeypatch.setattr(gradio_backend, "list_chunks", lambda **_: [{"id": "chunk-1"}])

    report = gradio_backend.preview_delete(str(source))

    assert report.dry_run is True
    assert report.file_exists is True
    assert report.file_deleted is False
    assert report.chunks_matched == 1
    assert source.exists()

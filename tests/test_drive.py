"""tests/test_drive.py — unit tests for optional Drive archival helpers."""

import config
from pipeline import drive


class _FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class _FakeFiles:
    def __init__(self):
        self.created = []
        self.queries = []
        self._next_id = 1

    def list(self, **kwargs):
        self.queries.append(kwargs)
        return _FakeRequest({"files": []})

    def create(self, **kwargs):
        body = kwargs.get("body", {})
        if "media_body" in kwargs:
            return _FakeRequest({"id": "file-id", "webViewLink": "https://drive/file-id"})

        created_id = f"folder-{self._next_id}"
        self._next_id += 1
        self.created.append((created_id, body))
        return _FakeRequest({"id": created_id})


class _FakeService:
    def __init__(self):
        self.fake_files = _FakeFiles()

    def files(self):
        return self.fake_files


def test_archive_file_returns_none_when_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DRIVE_ARCHIVE_ENABLED", False)
    path = tmp_path / "note.txt"
    path.write_text("hello")

    assert drive.archive_file(path, "document") is None


def test_archive_file_uploads_under_type_and_date_folders(tmp_path, monkeypatch):
    service = _FakeService()
    monkeypatch.setattr(config, "DRIVE_ARCHIVE_ENABLED", True)
    monkeypatch.setattr(config, "GOOGLE_DRIVE_ARCHIVE_ROOT_NAME", "archive")
    monkeypatch.setattr(config, "GOOGLE_DRIVE_ROOT_FOLDER_ID", None)
    monkeypatch.setattr(drive, "_get_service", lambda: service)

    path = tmp_path / "note.txt"
    path.write_text("hello")

    result = drive.archive_file(path, "document")

    assert result is not None
    assert result.file_id == "file-id"
    assert result.web_view_link == "https://drive/file-id"
    assert result.folder_id == "folder-4"
    assert result.folder_path.startswith("archive/document/")
    assert [body["name"] for _, body in service.fake_files.created[:2]] == ["archive", "document"]


def test_escape_query_value_escapes_backslashes_and_quotes():
    assert drive._escape_query_value(r"Bob's \ folder") == r"Bob\'s \\ folder"

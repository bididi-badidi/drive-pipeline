"""
tests/conftest.py — shared fixtures for drive-pipeline test suite.

Sets GOOGLE_API_KEY before any module-level config import, and provides
a temporary SQLite database so queue tests never touch the real one.
"""

import os

# Must be set before `import config` executes anywhere in the test session.
os.environ.setdefault("GOOGLE_API_KEY", "test-key")

import pytest  # noqa: E402


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Redirect the SQLite queue to a per-test temp file."""
    import config

    db = tmp_path / "test_jobs.db"
    monkeypatch.setattr(config, "SQLITE_DB_PATH", db)
    return db

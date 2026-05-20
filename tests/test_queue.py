"""tests/test_queue.py — unit tests for pipeline/queue.py"""

from pipeline import queue


def test_init_db_creates_table(tmp_db):
    queue.init_db()
    import sqlite3

    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
        ).fetchone()
    assert row is not None


def test_enqueue_returns_id(tmp_db, tmp_path):
    queue.init_db()
    job_id = queue.enqueue("file.pdf", tmp_path / "file.pdf", "document")
    assert isinstance(job_id, int)
    assert job_id >= 1


def test_enqueue_multiple_increments_id(tmp_db, tmp_path):
    queue.init_db()
    id1 = queue.enqueue("a.pdf", tmp_path / "a.pdf", "document")
    id2 = queue.enqueue("b.pdf", tmp_path / "b.pdf", "document")
    assert id2 > id1


def test_claim_pending_returns_oldest(tmp_db, tmp_path):
    queue.init_db()
    queue.enqueue("first.pdf", tmp_path / "first.pdf", "document")
    queue.enqueue("second.pdf", tmp_path / "second.pdf", "document")

    job = queue.claim_pending()
    assert job is not None
    assert job["filename"] == "first.pdf"
    assert job["status"] == "pending"  # row was fetched before the UPDATE


def test_claim_pending_marks_processing(tmp_db, tmp_path):
    import sqlite3

    queue.init_db()
    job_id = queue.enqueue("doc.pdf", tmp_path / "doc.pdf", "document")
    queue.claim_pending()

    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    assert row[0] == "processing"


def test_claim_pending_empty_queue_returns_none(tmp_db):
    queue.init_db()
    assert queue.claim_pending() is None


def test_mark_done(tmp_db, tmp_path):
    import sqlite3

    queue.init_db()
    job_id = queue.enqueue("done.pdf", tmp_path / "done.pdf", "document")
    queue.mark_done(job_id)

    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    assert row[0] == "done"


def test_mark_failed(tmp_db, tmp_path):
    import sqlite3

    queue.init_db()
    job_id = queue.enqueue("bad.pdf", tmp_path / "bad.pdf", "document")
    queue.mark_failed(job_id, "Something went wrong")

    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute("SELECT status, error FROM jobs WHERE id=?", (job_id,)).fetchone()
    assert row[0] == "failed"
    assert row[1] == "Something went wrong"

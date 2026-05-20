"""tests/test_watcher.py — unit tests for pipeline/watcher._detect_type"""

import pytest

from pipeline.watcher import _detect_type


def _make_file(tmp_path, name, content=""):
    p = tmp_path / name
    p.write_text(content)
    return p


# ── Document extensions ────────────────────────────────────────────────────────


def test_pdf_source_type(tmp_path):
    assert _detect_type(_make_file(tmp_path, "report.pdf")) == "pdf"


def test_md_source_type(tmp_path):
    assert _detect_type(_make_file(tmp_path, "notes.md", "# Hello")) == "md"


def test_docx_source_type(tmp_path):
    assert _detect_type(_make_file(tmp_path, "essay.docx")) == "docx"


def test_txt_plain_source_type(tmp_path):
    assert _detect_type(_make_file(tmp_path, "plain.txt", "just some text")) == "txt"


# ── URL detection from .txt ────────────────────────────────────────────────────


def test_txt_starting_with_http_is_url(tmp_path):
    p = _make_file(tmp_path, "link.txt", "https://example.com\nsome body text")
    assert _detect_type(p) == "url"


def test_txt_starting_with_http_no_trailing(tmp_path):
    p = _make_file(tmp_path, "link.txt", "http://example.com")
    assert _detect_type(p) == "url"


def test_txt_empty_file_is_txt(tmp_path):
    p = _make_file(tmp_path, "empty.txt", "")
    assert _detect_type(p) == "txt"


# ── .url extension ─────────────────────────────────────────────────────────────


def test_url_extension_is_url(tmp_path):
    assert _detect_type(_make_file(tmp_path, "bookmark.url", "URL=https://example.com")) == "url"


# ── Image extensions ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ["photo.jpg", "pic.jpeg", "image.png", "anim.gif", "photo.webp"])
def test_image_extensions(tmp_path, name):
    assert _detect_type(_make_file(tmp_path, name)) == "image"


# ── HTML extensions ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ["page.html", "page.htm"])
def test_html_extensions(tmp_path, name):
    assert _detect_type(_make_file(tmp_path, name, "<html></html>")) == "html"


# ── Unsupported ────────────────────────────────────────────────────────────────


def test_unsupported_extension_returns_none(tmp_path):
    assert _detect_type(_make_file(tmp_path, "archive.zip")) is None


def test_no_extension_returns_none(tmp_path):
    assert _detect_type(_make_file(tmp_path, "Makefile")) is None

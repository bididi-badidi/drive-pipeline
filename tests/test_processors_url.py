"""tests/test_processors_url.py — unit tests for processors/url.py"""

import pytest

from pipeline.processors.url import _parse_html, _read_url

# ── _read_url ──────────────────────────────────────────────────────────────────


def test_read_url_from_dot_url_file(tmp_path):
    p = tmp_path / "bookmark.url"
    p.write_text("[InternetShortcut]\nURL=https://example.com\n")
    assert _read_url(p) == "https://example.com"


def test_read_url_from_txt_http(tmp_path):
    p = tmp_path / "link.txt"
    p.write_text("https://example.com\nsome description")
    assert _read_url(p) == "https://example.com"


def test_read_url_from_txt_http_scheme(tmp_path):
    p = tmp_path / "link.txt"
    p.write_text("http://example.com")
    assert _read_url(p) == "http://example.com"


def test_read_url_no_url_raises(tmp_path):
    p = tmp_path / "note.txt"
    p.write_text("just some plain text\nno URL here")
    with pytest.raises(ValueError, match="No URL found"):
        _read_url(p)


def test_read_url_strips_whitespace(tmp_path):
    p = tmp_path / "link.txt"
    p.write_text("  https://example.com  \n")
    assert _read_url(p) == "https://example.com"


# ── _parse_html ────────────────────────────────────────────────────────────────


def test_parse_html_extracts_text():
    html = "<html><body><p>Hello world</p></body></html>"
    text = _parse_html(html)
    assert "Hello" in text
    assert "world" in text


def test_parse_html_strips_tags():
    html = "<h1>Title</h1><p>Body text here.</p>"
    text = _parse_html(html)
    assert "<" not in text
    assert ">" not in text


def test_parse_html_empty_body():
    html = "<html><body></body></html>"
    text = _parse_html(html)
    assert isinstance(text, str)


def test_parse_html_article_content():
    # readability-lxml favours article-like content
    html = """
    <html><body>
      <article>
        <h1>My Article</h1>
        <p>This is the main content of the article. It has enough words to be
        recognised as the main body by the readability algorithm.</p>
        <p>Second paragraph with more content to ensure extraction works.</p>
      </article>
      <nav><a href="/">Home</a><a href="/about">About</a></nav>
    </body></html>
    """
    text = _parse_html(html)
    assert "content" in text.lower() or "article" in text.lower()

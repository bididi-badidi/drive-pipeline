"""
pipeline/processors/url.py — HTTP fetch + Readability extraction.

Handles:
  • .url files  (Windows Internet Shortcut — reads the URL= line)
  • .txt files whose first line is a URL
  • .html / .htm local files
"""

from pathlib import Path

import httpx
from readability import Document


def extract(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in {".html", ".htm"}:
        html = path.read_text(errors="replace")
        return _parse_html(html)

    # Resolve the URL from the file content
    target_url = _read_url(path)
    html = _fetch(target_url)
    return _parse_html(html)


def _read_url(path: Path) -> str:
    text = path.read_text(errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("URL="):          # Windows .url shortcut
            return line[4:].strip()
        if line.startswith(("http://", "https://")):
            return line
    raise ValueError(f"No URL found in {path.name}")


def _fetch(url: str) -> str:
    headers = {"User-Agent": "drive-pipeline/0.1 (+local)"}
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


def _parse_html(html: str) -> str:
    doc = Document(html)
    # summary() returns cleaned HTML; strip tags for plain text
    from html.parser import HTMLParser

    class _Stripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self._parts: list[str] = []

        def handle_data(self, data: str) -> None:
            self._parts.append(data)

        def get_text(self) -> str:
            return " ".join(self._parts)

    stripper = _Stripper()
    stripper.feed(doc.summary())
    return stripper.get_text()

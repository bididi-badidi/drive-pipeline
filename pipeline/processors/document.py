"""
pipeline/processors/document.py — text extraction for PDF / DOCX / TXT / MD.
"""

from pathlib import Path


def extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf(path)
    if suffix == ".docx":
        return _docx(path)
    # .txt / .md — plain read
    return path.read_text(errors="replace")


def _pdf(path: Path) -> str:
    import fitz  # pymupdf

    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def _docx(path: Path) -> str:
    import docx  # python-docx

    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

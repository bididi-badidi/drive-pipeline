"""tests/test_processors_document.py — unit tests for processors/document.py."""

from pipeline.processors.document import extract


def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_txt_extract(tmp_path):
    p = _write(tmp_path, "note.txt", "Hello, world!")
    assert extract(p) == "Hello, world!"


def test_md_extract(tmp_path):
    content = "# Title\n\nSome **markdown** content."
    p = _write(tmp_path, "note.md", content)
    assert extract(p) == content


def test_txt_multiline(tmp_path):
    content = "line one\nline two\nline three"
    p = _write(tmp_path, "multi.txt", content)
    assert extract(p) == content


def test_txt_with_unicode(tmp_path):
    content = "Héllo wörld — ñoño"
    p = _write(tmp_path, "unicode.txt", content)
    assert extract(p) == content


def test_txt_empty_file(tmp_path):
    p = _write(tmp_path, "empty.txt", "")
    assert extract(p) == ""


def test_pdf_extract(tmp_path):
    import fitz

    p = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PDF document content")
    doc.save(p)
    doc.close()

    assert "PDF document content" in extract(p)


def test_docx_extract(tmp_path):
    import docx

    p = tmp_path / "sample.docx"
    doc = docx.Document()
    doc.add_paragraph("DOCX document content")
    doc.save(p)

    assert extract(p) == "DOCX document content"

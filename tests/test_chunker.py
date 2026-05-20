"""tests/test_chunker.py — unit tests for pipeline/chunker.py"""

from pipeline.chunker import chunk_for_source, chunk_markdown, chunk_pdf, chunk_text


def test_empty_string_returns_empty():
    assert chunk_text("") == []


def test_whitespace_only_returns_empty():
    assert chunk_text("   \n\t  ") == []


def test_short_text_single_chunk():
    text = "Hello world this is a short piece of text."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text.strip()


def test_long_text_produces_multiple_chunks(monkeypatch):
    import config

    # Small window so a long text produces several chunks
    monkeypatch.setattr(config, "CHUNK_SIZE", 10)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 2)

    # 50 words → should produce several chunks
    words = ["word"] * 50
    text = " ".join(words)
    chunks = chunk_text(text)
    assert len(chunks) > 1


def test_chunks_overlap(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 10)  # ~7 words
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 4)  # ~3 words overlap

    words = [str(i) for i in range(30)]
    text = " ".join(words)
    chunks = chunk_text(text)

    # overlap_words mirrors the chunker's own calculation
    overlap_words = max(0, int(config.CHUNK_OVERLAP / 1.33))

    # First `overlap_words` of chunk N+1 must equal last `overlap_words` of chunk N
    for i in range(len(chunks) - 1):
        end_words = chunks[i].split()[-overlap_words:]
        start_words = chunks[i + 1].split()[:overlap_words]
        assert end_words == start_words, (
            f"No overlap between chunk {i} and {i + 1}: {end_words!r} vs {start_words!r}"
        )


def test_all_words_covered(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 10)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 2)

    words = [str(i) for i in range(40)]
    text = " ".join(words)
    chunks = chunk_text(text)

    # Every word from the original text must appear in at least one chunk
    all_chunk_words = set(w for c in chunks for w in c.split())
    assert set(words) == all_chunk_words


def test_chunk_for_source_routes_txt_to_plain_text(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 10)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 2)

    text = " ".join(str(i) for i in range(30))
    assert chunk_for_source(text, "txt") == chunk_text(text)


def test_chunk_for_source_routes_legacy_document_to_plain_text(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 10)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 2)

    text = " ".join(str(i) for i in range(30))
    assert chunk_for_source(text, "document") == chunk_text(text)


def test_markdown_keeps_normal_sized_sections_together(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 80)

    text = "# One\n\nFirst paragraph.\n\n## Two\n\nSecond paragraph."
    chunks = chunk_markdown(text)

    assert chunks == ["# One\n\nFirst paragraph.", "## Two\n\nSecond paragraph."]


def test_markdown_keeps_fenced_code_block_intact(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 22)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 0)

    text = "\n".join(
        [
            "# Notes",
            "",
            "intro words " * 8,
            "",
            "```python",
            "def hello():",
            "    return 'world'",
            "```",
            "",
            "outro words " * 8,
        ]
    )

    chunks = chunk_markdown(text)

    code_chunks = [chunk for chunk in chunks if "def hello" in chunk]
    assert len(code_chunks) == 1
    assert "```python\ndef hello():\n    return 'world'\n```" in code_chunks[0]


def test_markdown_oversized_section_carries_heading_context(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 10)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 0)

    text = "# Big Section\n\n" + " ".join(str(i) for i in range(50))
    chunks = chunk_markdown(text)

    assert len(chunks) > 1
    assert all(chunk.startswith("# Big Section") for chunk in chunks)


def test_docx_strategy_keeps_paragraphs_when_possible(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 12)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 0)

    text = "first paragraph has words\n\nsecond paragraph has words\n\nthird paragraph has words"
    chunks = chunk_for_source(text, "docx")

    assert chunks == [
        "first paragraph has words\n\nsecond paragraph has words",
        "third paragraph has words",
    ]


def test_pdf_strategy_uses_page_markers_as_boundaries(monkeypatch):
    import config

    monkeypatch.setattr(config, "CHUNK_SIZE", 10)
    monkeypatch.setattr(config, "CHUNK_OVERLAP", 0)

    text = "--- Page 1 ---\nalpha beta gamma\n\n--- Page 2 ---\ndelta epsilon zeta"
    chunks = chunk_pdf(text)

    assert chunks == ["--- Page 1 ---\nalpha beta gamma", "--- Page 2 ---\ndelta epsilon zeta"]

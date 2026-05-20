"""tests/test_chunker.py — unit tests for pipeline/chunker.py"""

from pipeline.chunker import chunk_text


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

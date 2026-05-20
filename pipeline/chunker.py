"""
pipeline/chunker.py — token-aware text chunking with overlap.

Uses a simple word-count proxy for token count (≈ 0.75 tokens/word)
so there are no hard dependencies on a tokenizer at skeleton stage.
Swap the `_token_len` function for tiktoken or sentencepiece as needed.
"""

import re

import config

PAGE_MARKER_RE = re.compile(r"^--- Page \d+ ---$", re.MULTILINE)


def _token_len(text: str) -> int:
    """Rough token estimate: word count × 1.33 (words are ~0.75 tokens each)."""
    words = len(re.findall(r"\S+", text))
    return int(words * 1.33)


def chunk_text(text: str) -> list[str]:
    """
    Split `text` into overlapping chunks of roughly CHUNK_SIZE tokens.

    Returns a list of chunk strings. An empty or whitespace-only input
    returns an empty list.
    """
    text = text.strip()
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    # Convert token budget to approximate word budget
    size_words = max(1, int(config.CHUNK_SIZE / 1.33))
    overlap_words = max(0, int(config.CHUNK_OVERLAP / 1.33))
    step = max(1, size_words - overlap_words)

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + size_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += step

    return chunks


def chunk_for_source(text: str, source_type: str | None) -> list[str]:
    """Route extracted text to the best chunking strategy for its source type."""
    if source_type == "md":
        return chunk_markdown(text)
    if source_type == "docx":
        return chunk_blocks(text)
    if source_type == "pdf":
        return chunk_pdf(text)
    return chunk_text(text)


def chunk_blocks(text: str) -> list[str]:
    """
    Chunk paragraph-like text while preserving block boundaries when possible.

    This is useful for DOCX extraction, where paragraphs are the most reliable
    structure currently preserved by the processor.
    """
    blocks = _split_paragraph_blocks(text)
    return _pack_blocks(blocks)


def chunk_pdf(text: str) -> list[str]:
    """Chunk PDF text using inserted page markers as preferred boundaries."""
    text = text.strip()
    if not text:
        return []

    if not PAGE_MARKER_RE.search(text):
        return chunk_text(text)

    pages = _split_pdf_pages(text)
    return _pack_blocks(pages)


def chunk_markdown(text: str) -> list[str]:
    """Chunk Markdown by sections and blocks instead of plain word windows."""
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    for section in _split_markdown_sections(text):
        if _token_len(section) <= config.CHUNK_SIZE:
            chunks.append(section)
            continue

        heading_context = _heading_context(section)
        section_chunks = _pack_blocks(
            _split_markdown_blocks(section), heading_context=heading_context
        )
        chunks.extend(section_chunks)

    return chunks


def _split_paragraph_blocks(text: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n+", text.strip()) if block.strip()]


def _pack_blocks(blocks: list[str], heading_context: str = "") -> list[str]:
    blocks = [block.strip() for block in blocks if block.strip()]
    if not blocks:
        return []

    chunks: list[str] = []
    current: list[str] = []

    for block in blocks:
        candidate = "\n\n".join([*current, block]) if current else block
        if _token_len(candidate) <= config.CHUNK_SIZE:
            current.append(block)
            continue

        if current:
            chunks.append(_with_heading_context("\n\n".join(current), heading_context))
            current = []

        if _token_len(block) <= config.CHUNK_SIZE:
            current.append(block)
        else:
            for split_chunk in chunk_text(block):
                chunks.append(_with_heading_context(split_chunk, heading_context))

    if current:
        chunks.append(_with_heading_context("\n\n".join(current), heading_context))

    return chunks


def _with_heading_context(chunk: str, heading_context: str) -> str:
    if not heading_context:
        return chunk
    if chunk.startswith(heading_context):
        return chunk
    return f"{heading_context}\n\n{chunk}"


def _split_pdf_pages(text: str) -> list[str]:
    pages: list[str] = []
    current: list[str] = []

    for line in text.splitlines():
        if PAGE_MARKER_RE.match(line.strip()) and current:
            pages.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        pages.append("\n".join(current).strip())

    return pages


def _split_markdown_sections(text: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    in_fence = False

    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence

        if not in_fence and _is_markdown_heading(line) and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    return [section for section in sections if section]


def _split_markdown_blocks(section: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    mode: str | None = None
    in_fence = False

    for line in section.splitlines():
        stripped = line.strip()

        if stripped.startswith(("```", "~~~")):
            if not in_fence:
                _flush_block(blocks, current)
                current = [line]
                mode = "fence"
                in_fence = True
            else:
                current.append(line)
                _flush_block(blocks, current)
                current = []
                mode = None
                in_fence = False
            continue

        if in_fence:
            current.append(line)
            continue

        next_mode = _markdown_block_mode(line)
        if not stripped:
            _flush_block(blocks, current)
            current = []
            mode = None
            continue

        if mode and next_mode != mode:
            _flush_block(blocks, current)
            current = []

        current.append(line)
        mode = next_mode

    _flush_block(blocks, current)
    return blocks


def _flush_block(blocks: list[str], lines: list[str]) -> None:
    block = "\n".join(lines).strip()
    if block:
        blocks.append(block)


def _markdown_block_mode(line: str) -> str:
    stripped = line.strip()
    if _is_markdown_heading(line):
        return "heading"
    if re.match(r"^([-*+]|\d+\.)\s+", stripped):
        return "list"
    if stripped.startswith("|"):
        return "table"
    return "paragraph"


def _is_markdown_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+\S", line))


def _heading_context(section: str) -> str:
    headings = []
    for line in section.splitlines():
        if _is_markdown_heading(line):
            headings.append(line.strip())
        elif line.strip():
            break
    return "\n".join(headings)

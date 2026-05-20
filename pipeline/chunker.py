"""
pipeline/chunker.py — token-aware text chunking with overlap.

Uses a simple word-count proxy for token count (≈ 0.75 tokens/word)
so there are no hard dependencies on a tokenizer at skeleton stage.
Swap the `_token_len` function for tiktoken or sentencepiece as needed.
"""

import re

import config


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

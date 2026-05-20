"""
pipeline/embedder.py — Gemini text-embedding-004 embeddings.
"""

import google.generativeai as genai

import config

genai.configure(api_key=config.GOOGLE_API_KEY)


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Embed a list of text chunks.
    Returns a parallel list of embedding vectors.
    """
    if not chunks:
        return []

    result = genai.embed_content(
        model=config.EMBEDDING_MODEL,
        content=chunks,
        task_type="retrieval_document",
    )
    return result["embedding"]


def embed_query(query: str) -> list[float]:
    """Embed a single query string for retrieval."""
    result = genai.embed_content(
        model=config.EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]

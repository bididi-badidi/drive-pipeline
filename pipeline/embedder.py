"""
pipeline/embedder.py — Local bge-m3 embeddings via sentence-transformers.
"""

from __future__ import annotations

from sentence_transformers import SentenceTransformer

import config

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(
            config.EMBEDDING_MODEL,
            cache_folder=str(config.MODEL_CACHE_DIR),
        )
    return _model


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Embed a list of text chunks.
    Returns a parallel list of embedding vectors.
    """
    if not chunks:
        return []

    model = _get_model()
    vectors = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string for retrieval."""
    model = _get_model()
    vector = model.encode(query, normalize_embeddings=True, show_progress_bar=False)
    return vector.tolist()

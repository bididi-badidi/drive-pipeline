"""
pipeline/vector_store.py — ChromaDB initialisation, upsert, and query helpers.
"""

import chromadb

import config

_client: chromadb.PersistentClient | None = None
_COLLECTION_NAME = "drive_pipeline"


def _get_collection() -> chromadb.Collection:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(config.CHROMA_PERSIST_DIR))
    return _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    metadata_list: list[dict],
) -> None:
    """Upsert a batch of chunks with pre-computed embeddings."""
    if not chunks:
        return

    collection = _get_collection()
    ids = [m["chunk_id"] for m in metadata_list]
    # ChromaDB metadata values must be str | int | float | bool
    safe_meta = [_sanitise(m) for m in metadata_list]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=safe_meta,
    )


def query(
    query_embedding: list[float],
    n_results: int = 10,
    where: dict | None = None,
) -> list[dict]:
    """
    Return the top-n most similar chunks.
    Each result dict has keys: id, document, metadata, distance.
    """
    collection = _get_collection()
    kwargs: dict = {"query_embeddings": [query_embedding], "n_results": n_results}
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)
    return [
        {
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        }
        for i in range(len(results["ids"][0]))
    ]


def _sanitise(meta: dict) -> dict:
    """Convert non-primitive metadata values to strings for ChromaDB."""
    out: dict = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out

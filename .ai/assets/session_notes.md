# Session Handover Notes

## 2026-05-20 — v1 complete, smoke-test passed

v1 is fully working. Two bugs were found and fixed during smoke-testing:

1. `vector_store.py` — `chromadb.PersistentClient` is a factory function (not a class),
   so `_client: chromadb.PersistentClient | None` blew up at import. Fixed with
   `from __future__ import annotations`.

2. `config.py` — Both Gemini model names were stale:
   - `text-embedding-004` → `gemini-embedding-001`
   - `gemini-1.5-flash` → `gemini-2.0-flash`

Smoke-test result: `.txt` file dropped into originals/ → picked up by watcher →
enqueued → extracted → 1 chunk embedded (3072-dim) → stored in ChromaDB ✓

`google-generativeai` still emits a FutureWarning about deprecation in favour of
`google-genai`. The package works fine for now. Migration to `google.genai` SDK
is a natural v2 task (backlogged).

## 2026-05-20 — Embedding model dimension guard

Chroma collection names are now derived from `EMBEDDING_MODEL` by default.
This prevents `InvalidArgumentError: Collection expecting embedding with
dimension of 3072, got 1024` after switching from Gemini embeddings to local
`BAAI/bge-m3`. The old 3072-dim collection remains intact, and new BGE vectors
go into a separate collection.

Set `CHROMA_COLLECTION_NAME` only when intentionally forcing a specific Chroma
collection. To retry Job #7, move the failed source file back into
`~/Documents/toDrive/originals/` or reset/requeue that job in SQLite.

Next session: start v2 — Drive archive integration (`pipeline/drive.py`).

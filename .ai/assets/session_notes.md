# Session Handover Notes

## 2026-05-20 — Document type chunking implemented

Implemented concrete document chunking from the branch plan:
`.ai/assets/branches/feat-doc-type-support/document-type-chunking-plan.md`.

Current code maps `.pdf`, `.docx`, `.txt`, and `.md` to concrete source types
and `pipeline/worker.py` sends extracted text through `chunk_for_source()`.

Markdown extraction remains a plain file read, but Markdown chunking is now
structure-aware and preserves headings, fenced code blocks, lists, tables, and
paragraphs where possible. `.txt` keeps the current overlapping word-window
behavior.

`source_type="document"` is still supported as a legacy alias in the worker and
falls back to plain text chunking for any already queued rows.

Validation completed:
- `uv run ruff format .`
- `uv run ruff check . --fix`
- `uv run pytest` (63 passed)

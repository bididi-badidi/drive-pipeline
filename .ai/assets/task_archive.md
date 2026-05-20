# Task Archive

## 2026-05-20

- [x] Document type chunking support ([plan](branches/feat-doc-type-support/document-type-chunking-plan.md))
  - Added concrete document source types: `pdf`, `docx`, `txt`, and `md`.
  - Routed chunking by source type in `pipeline/chunker.py`.
  - Kept `.txt` on the existing overlapping word-window strategy.
  - Added Markdown-aware chunking for headings, fenced code blocks, lists, tables, and paragraphs.
  - Added paragraph-aware DOCX chunking and page-aware PDF chunking.

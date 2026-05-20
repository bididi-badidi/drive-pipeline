# Document Type Chunking Plan

## Goal

Support four document-specific chunking paths for `pdf`, `docx`, `txt`, and `md`, with Markdown using a structure-aware strategy instead of the plain text word-window chunker.

## Task Type

Hybrid: source type detection and metadata changes are sequential foundations; individual chunking strategies and tests can be built in parallel once the public chunker API is defined.

## Current State

- `pipeline/watcher.py` maps `.pdf`, `.docx`, `.txt`, and `.md` to a single `source_type="document"` value.
- `pipeline/processors/document.py` extracts all document formats through one `extract(path)` function.
- `pipeline/worker.py` calls `chunk_text(text)` for every processor result, so URLs, HTML, OCR text, PDFs, DOCX, TXT, and Markdown all share the same word-window strategy.
- `pipeline/metadata.py` stores only the broad `source_type`, which makes it hard to filter document chunks by concrete document format.

## Proposed Behavior

| Extension | Source type | Extraction | Chunking strategy |
|---|---|---|---|
| `.pdf` | `pdf` | PyMuPDF page text | Page-aware text chunking with page boundary hints preserved where practical |
| `.docx` | `docx` | `python-docx` paragraphs | Paragraph-aware text chunking that avoids splitting paragraphs until size limits require it |
| `.txt` | `txt` | Plain text read | Existing overlapping word-window text chunking |
| `.md` | `md` | Plain text read | Markdown structure-aware chunking by headings, fenced code blocks, lists, and paragraphs |

URLs, HTML, and images can continue using the generic text chunker for now unless a later task gives them their own strategies.

## Subtasks

[1] Define source type contract
- Input: `config.py`, `pipeline/watcher.py`, queue schema expectations, metadata schema.
- Action: Replace broad document source type with concrete `pdf`, `docx`, `txt`, and `md` values while preserving URL detection for `.txt` files whose first line is an HTTP(S) URL.
- Output: Clear source type contract documented in code/tests.
- Success: Watcher tests prove each supported document extension gets the expected source type.
- Depends on: none

[2] Define chunker API
- Input: Current `chunk_text(text)` usage in `pipeline/worker.py`.
- Action: Introduce a routing API such as `chunk_document(text, source_type)` or `chunk_text(text, source_type="txt")`, while keeping `chunk_text(text)` available for existing URL/image callers if useful.
- Output: One worker call site that selects the right chunking strategy from `source_type`.
- Success: Worker can route `pdf`, `docx`, `txt`, and `md` without branching across processor modules.
- Depends on: [1]

[3] Implement Markdown chunker
- Input: Raw Markdown text.
- Action: Parse Markdown into structure blocks using lightweight line-based parsing:
  - keep ATX headings with their following section content;
  - keep fenced code blocks intact;
  - keep list runs together when possible;
  - split oversized sections with the existing token-window fallback;
  - add small overlap between adjacent Markdown sections by carrying heading context rather than arbitrary word overlap.
- Output: `chunk_markdown(text)` strategy.
- Success: Tests show headings/code fences are not broken by normal-sized chunks, and oversized sections still split safely.
- Depends on: [2]

[4] Implement TXT strategy
- Input: Existing `chunk_text(text)`.
- Action: Preserve current overlapping word-window behavior for `.txt`.
- Output: Stable `chunk_plain_text(text)` or retained `chunk_text(text)` strategy.
- Success: Existing chunker tests continue to pass.
- Depends on: [2]

[5] Implement DOCX paragraph strategy
- Input: Extracted DOCX paragraphs joined by newlines.
- Action: Build chunks from paragraph blocks first, only falling back to word-window splitting for paragraphs or paragraph groups that exceed the token budget.
- Output: `chunk_docx(text)` strategy.
- Success: Tests prove normal paragraphs stay intact and oversized paragraphs are split with overlap.
- Depends on: [2]

[6] Implement PDF page-aware strategy
- Input: Extracted PDF text.
- Action: Preserve page boundaries during extraction or insert page delimiters, then chunk by page/page paragraph before falling back to word-window splitting for oversized pages.
- Output: `chunk_pdf(text)` strategy and, if needed, extraction output that carries page boundaries.
- Success: Tests prove chunks do not unnecessarily merge unrelated page text and oversized pages still split.
- Depends on: [2]

[7] Update metadata and tests
- Input: Concrete source types and chunk outputs.
- Action: Ensure `source_type` metadata stores `pdf`, `docx`, `txt`, or `md`; add tests for watcher detection, chunk routing, and markdown-specific behavior.
- Output: Regression coverage for all four document type paths.
- Success: Relevant unit tests pass locally.
- Depends on: [1], [3], [4], [5], [6]

[8] Documentation and migration notes
- Input: Updated behavior and public configuration.
- Action: Update `.ai/assets/PLAN.md` and any README section that describes supported file types or metadata values.
- Output: Docs reflect concrete document types and Markdown-specific chunking.
- Success: A new contributor can tell that `.md` no longer uses plain text chunking.
- Depends on: [7]

## Dependency Map

```text
[1] -> [2] -> [3] --\
             -> [4] ---\
             -> [5] ----> [7] -> [8]
             -> [6] ---/
```

Ready to start: [1]

## Design Notes

- Prefer routing chunking by `source_type` in `pipeline/chunker.py`; processors should stay focused on extraction.
- Keep the existing `chunk_text(text)` function as the generic fallback to limit blast radius.
- Use source types that match metadata and future retrieval filters: `pdf`, `docx`, `txt`, `md`, `image`, `url`, `html`.
- Markdown should not be treated as "plain read plus plain chunk." Plain read is fine for extraction, but chunking should preserve document structure.
- Avoid adding a heavy Markdown parser unless tests show line-based parsing is too brittle for expected notes. A small parser is likely enough for personal notes, READMEs, and copied Markdown documents.

## Risks / Unknowns

- PDF extraction currently returns one joined string, so page-aware chunking may require changing `_pdf()` to include page delimiters or returning structured extraction data.
- DOCX extraction currently loses heading style and list metadata. Paragraph-aware chunking is still useful, but true section-aware DOCX chunking would require richer extraction.
- Concrete `source_type` values may affect existing queued jobs that still say `document`; the worker should either support `document` as a legacy alias or fail with a clear migration path.
- Markdown table handling is not specified. Initial implementation should keep contiguous table rows together as paragraph-like blocks.

## Acceptance Criteria

- `.pdf`, `.docx`, `.txt`, and `.md` jobs are distinguishable in queue records and chunk metadata.
- `.md` files use Markdown-aware chunking and preserve normal-sized headings, lists, tables, and fenced code blocks.
- `.txt` files keep the current overlapping word-window behavior.
- Existing URL detection for `.txt` first-line URLs still works.
- Unit tests cover detection, routing, Markdown chunking, and at least one PDF/DOCX/TXT strategy behavior.

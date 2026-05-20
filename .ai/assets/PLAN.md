# drive-pipeline (Mac Poller) — Project Plan

## Role in the System

This project is the **Mac poller** — the local processing engine.
It is one half of a two-part system:

| Component | Repo | Responsibility |
|---|---|---|
| Telegram bot | separate project | Accept input from user (photos, docs, text, URLs), drop raw files into `~/toDrive/originals/` |
| **Mac poller** | **this repo** | Watch `originals/`, queue jobs in SQLite, process by type, chunk, embed, store in ChromaDB |

---

## Directory Contract

```
~/Documents/toDrive/
  originals/    raw files land here (written by Telegram bot or manual drop)
  processing/   file moves here while being worked on
  failed/       file moves here on error, with a .error.txt log alongside it
```

The poller owns `processing/` and `failed/`. The bot (or user) only writes to `originals/`.

---

## Pipeline Flow

```
originals/ (new file detected by watcher)
  ↓  INSERT job into SQLite (status=pending)
  ↓  move file to processing/
Worker picks up pending job
  ↓
Detect type → dispatch to processor
  ├── URL (.url / .txt starting with http)  → HTTP fetch + Readability
  ├── PDF (.pdf)                            → PyMuPDF page text
  ├── DOCX (.docx)                          → python-docx paragraphs
  ├── Text (.txt)                           → plain read
  ├── Markdown (.md)                        → plain read
  └── Image (.jpg .png .webp .gif)          → OCR (Gemini Vision)
  ↓
Chunker     — routes by source type; Markdown is structure-aware
  ↓
Metadata    — filename, source_type, chunk_index, total_chunks, created_at
  ↓
Embedder    — Gemini text-embedding-004
  ↓
ChromaDB    — upsert chunks + embeddings + metadata
  ↓  success
UPDATE job status=done
move file back to originals/ (or delete from processing/)
```

On any error → UPDATE job status=failed, move file to `failed/`, write `.error.txt`.

---

## SQLite Job Queue Schema

```sql
CREATE TABLE jobs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  filename    TEXT NOT NULL,
  source_path TEXT NOT NULL,
  source_type TEXT,           -- pdf | docx | txt | md | image | url | html
  status      TEXT DEFAULT 'pending',  -- pending | processing | done | failed
  error       TEXT,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
```

---

## Supported File Types

| Type | Extensions | Processor |
|---|---|---|
| PDF | `.pdf` | `pymupdf` |
| Office docs | `.docx` | `python-docx` |
| Plain text / notes | `.txt` | built-in `open()` |
| Markdown | `.md` | built-in `open()` |
| Images | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif` | Gemini Vision (OCR) |
| URLs | `.url`, or `.txt` whose first line is a URL | `httpx` + `readability-lxml` |
| HTML | `.html`, `.htm` | `beautifulsoup4` |

---

## Metadata Schema (per chunk)

```json
{
  "chunk_id":     "uuid4",
  "job_id":       1,
  "filename":     "original_filename.pdf",
  "source_path":  "/Users/user/Documents/toDrive/originals/original_filename.pdf",
  "source_type":  "pdf | docx | txt | md | image | url | html",
  "chunk_index":  0,
  "total_chunks": 7,
  "created_at":   "2026-05-20T10:00:00Z",
  "tags":         []
}
```

---

## Module Layout

```
drive-pipeline/
├── main.py                       entry point — starts watcher + worker loop
├── config.py                     env vars, directory paths, constants
├── pipeline/
│   ├── __init__.py
│   ├── watcher.py                watchdog observer — detects new files in originals/
│   ├── queue.py                  SQLite job queue (insert, claim, update status)
│   ├── worker.py                 main loop — polls queue, dispatches by type
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── url.py                HTTP fetch + Readability extraction
│   │   ├── document.py           PDF / txt / md / docx extraction
│   │   └── image.py              OCR via Gemini Vision
│   ├── chunker.py                source-aware chunking strategies
│   ├── metadata.py               metadata dict builder
│   ├── embedder.py               Gemini text-embedding-004
│   └── vector_store.py           ChromaDB init, upsert, query helpers
├── .env                          GOOGLE_API_KEY, paths
└── pyproject.toml
```

---

## Config / Env Vars

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key (embeddings + Vision) |
| `WATCH_DIR` | Root toDrive path (default `~/Documents/toDrive`) |
| `CHROMA_PERSIST_DIR` | Local ChromaDB storage path |
| `SQLITE_DB_PATH` | SQLite file path (default `~/.drive-pipeline/jobs.db`) |

---

## Milestones

### v1 — Core Pipeline (this repo)
- [ ] `config.py` — paths, env loading
- [ ] `pipeline/queue.py` — SQLite job queue
- [ ] `pipeline/watcher.py` — originals/ watcher, enqueues jobs
- [ ] `pipeline/processors/document.py` — PDF / text / markdown
- [ ] `pipeline/processors/image.py` — OCR via Gemini Vision
- [ ] `pipeline/processors/url.py` — HTTP fetch + Readability
- [ ] `pipeline/chunker.py` — token chunker
- [ ] `pipeline/metadata.py` — metadata builder
- [ ] `pipeline/embedder.py` — Gemini embeddings
- [ ] `pipeline/vector_store.py` — ChromaDB upsert
- [ ] `pipeline/worker.py` — job dispatcher
- [ ] `main.py` — wires watcher + worker

### v2 — Enrichment + Drive Archive
- [ ] `pipeline/drive.py` — Google Drive upload + folder structure
- [ ] Playwright fallback for JS-heavy URLs
- [ ] Duplicate detection by content hash and canonical URL
- [ ] Browser/mobile share shortcut integration

### v3 — Intelligence
- [ ] Summarization per document
- [ ] Backlinking between screenshot + URL + notes
- [ ] Re-crawl option for stale URLs

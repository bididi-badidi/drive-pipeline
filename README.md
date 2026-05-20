# drive-pipeline — Personal AI Memory OS

A self-hosted RAG pipeline that turns Google Drive into a semantic, agent-accessible long-term memory store. Files uploaded from any device are automatically extracted, chunked, embedded, and indexed for hybrid search and LLM-augmented retrieval.

---

## Architecture Overview

### Ingestion Flow

```
Phone / Client
  ↓
Agent (MCP client)
  ↓
Upload file / note
  ↓
Google Drive  ←── source of truth
  ↓
Background worker detects new file
  ↓
Text extraction  (PDF → pymupdf, DOCX → python-docx, Audio → Whisper, OCR → Tesseract)
  ↓
Chunking  (300–800 tokens, 50–100 token overlap)
  ↓
Embedding  (OpenAI text-embedding-3-small  or  local BGE/E5 model)
  ↓
Store in:
    ├── Vector DB   (Qdrant — semantic + metadata)
    └── Keyword index  (BM25 via Qdrant sparse vectors)
  ↓
Metadata record points back to Drive file ID
```

### Retrieval Flow

```
User query
  ↓
Embed query
  ↓
Hybrid search  (semantic similarity + BM25 keyword scoring)
  ↓
Optional reranking
  ↓
Fetch original Drive file if full document needed
  ↓
Assemble context
  ↓
LLM response
```

---

## Core Components

### 1. Storage Layer — Google Drive

| Property | Detail |
|---|---|
| Role | Durable source-of-truth for all files |
| API | Google Drive API v3 |
| Reference key | Drive file ID |

> Drive behaves like object storage (upload/download/metadata/permissions) but has API quotas and is slower than S3. Well-suited for personal-scale AI memory systems.

---

### 2. Vector Store — Qdrant (recommended)

| Option | Best for | Notes |
|---|---|---|
| **Qdrant** | Production, self-hosted | Fast, hybrid search, metadata filtering |
| Weaviate | Managed hybrid search | Built-in BM25 + vector |
| ChromaDB | Local prototyping | Simple but weaker hybrid retrieval |

Qdrant is the default choice: self-hostable, production-grade, and supports both dense vector search and sparse BM25 in a single query.

---

### 3. Embedding Model

**Option A — OpenAI (default)**
```
model: text-embedding-3-small
```
High quality, cheap, simple API. Good starting point.

**Option B — Local**
```
sentence-transformers: all-MiniLM-L6-v2 / bge-small-en / e5-small-v2
```
Privacy-preserving, offline-capable, zero recurring cost.

---

### 4. Background Worker

The ingestion agent does **not** parse files or generate embeddings inline. It creates a task and hands off immediately.

```
Agent  →  creates ingestion task  →  background worker processes task
```

Worker responsibilities:
1. Poll for new Drive files
2. Download from Drive
3. Extract text
4. Chunk content
5. Generate embeddings
6. Store vectors + sparse index
7. Update status metadata

---

### 5. Text Extraction

| Content type | Library |
|---|---|
| PDF | `pymupdf`, `pdfplumber` |
| DOCX | `python-docx` |
| OCR | `tesseract`, Google Vision API |
| Audio | `whisper` |

---

### 6. Hybrid Search

Vector search alone degrades on exact filenames, IDs, error codes, rare entities, and technical terms. BM25 keyword scoring fills that gap.

```
final_score = α × semantic_similarity + (1 − α) × BM25_score
```

---

### 7. Metadata Schema

Each stored chunk carries:

```json
{
  "chunk_id": "...",
  "file_id": "...",
  "drive_path": "...",
  "text": "...",
  "embedding": [...],
  "keywords": [...],
  "created_at": "...",
  "source_type": "pdf",
  "tags": ["finance", "invoice"]
}
```

Rich metadata enables filtering by time, tag, source type, and Drive path — critical for retrieval quality at scale.

---

### 8. MCP Role

MCP acts as the **wiring layer** — it is not the vector database or the memory store itself.

Responsibilities:
- Orchestrate tool calls between agent, Drive, and retrieval pipeline
- Expose retrieval as callable tools to the agent
- Coordinate automation and scheduled ingestion

---

### 9. Phone-First Architecture

Phones are input devices, not workers. They are not suited for long-running workers, local vector DB hosting, or OCR pipelines.

```
Phone  →  Agent UI  →  Cloud VM / Home Server / Raspberry Pi
```

---

## Recommended Full Stack

| Layer | Choice |
|---|---|
| File storage | Google Drive |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector DB | Qdrant (self-hosted) |
| Backend API | FastAPI |
| Background worker | Python async worker |
| Orchestration | MCP |
| Retrieval | Hybrid search (dense + BM25) |

## MVP Stack (fastest path to working prototype)

| Layer | Choice |
|---|---|
| File storage | Google Drive |
| Embeddings | OpenAI Embeddings API |
| Vector DB | ChromaDB |
| Framework | LangChain or LlamaIndex |

---

## Design Principles

- **Never store full files in the vector DB.** Store chunks + embeddings + metadata + Drive references. Original files live in Drive.
- **Chunking quality matters.** Use 300–800 token chunks with 50–100 token overlap. Poor chunking significantly degrades retrieval.
- **Metadata is not optional.** Tags, timestamps, source type, and Drive path enable filtering and time-aware search that pure vector similarity cannot provide.
- **Decouple the agent from heavy processing.** The agent creates tasks; the worker does the work. This keeps the agent responsive and stateless.

---

## Project Structure

```
drive-pipeline/
├── main.py              # entry point
├── pyproject.toml       # project metadata and dependencies
├── README.md            # this file
├── .ai/assets/          # project planning and session notes
└── .claude/             # Claude Code memory and config
```

## Development

Install the local pre-commit hooks before committing:

```bash
uv run pre-commit install
```

Run all hooks manually with:

```bash
uv run pre-commit run --all-files
```

The hook suite checks for leaked secrets, fixes trailing whitespace / EOF issues,
and runs Ruff linting + formatting through the project environment.

---

## Goal

This pipeline forms the foundation of a **Personal AI Memory OS** — a system with persistent memory, semantic retrieval, automated knowledge indexing, and agent-accessible long-term context over all your personal documents.

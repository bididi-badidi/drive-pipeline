"""
config.py — centralised settings loaded from environment / .env file.
All other modules import from here; nothing reads os.environ directly.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _expand(raw: str | None, default: str) -> Path:
    return Path(os.path.expanduser(raw or default))


# ── Gemini ────────────────────────────────────────────────────────────────────
GOOGLE_API_KEY: str = os.environ["GOOGLE_API_KEY"]

# ── Directory layout ──────────────────────────────────────────────────────────
WATCH_DIR: Path = _expand(os.getenv("WATCH_DIR"), "~/Documents/toDrive")
ORIGINALS_DIR: Path = WATCH_DIR / "originals"
PROCESSING_DIR: Path = WATCH_DIR / "processing"
FAILED_DIR: Path = WATCH_DIR / "failed"

# ── Persistence ───────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: Path = _expand(
    os.getenv("CHROMA_PERSIST_DIR"), "~/.drive-pipeline/chroma"
)
SQLITE_DB_PATH: Path = _expand(
    os.getenv("SQLITE_DB_PATH"), "~/.drive-pipeline/jobs.db"
)

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 512        # target tokens per chunk
CHUNK_OVERLAP: int = 64      # overlap tokens between adjacent chunks

# ── Gemini model IDs ──────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "models/text-embedding-004"
VISION_MODEL: str = "models/gemini-1.5-flash"

# ── Supported extensions (lower-case) ─────────────────────────────────────────
DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".txt", ".md", ".docx"})
IMAGE_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})
URL_EXTENSIONS: frozenset[str] = frozenset({".url"})
HTML_EXTENSIONS: frozenset[str] = frozenset({".html", ".htm"})

ALL_SUPPORTED_EXTENSIONS: frozenset[str] = (
    DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS | URL_EXTENSIONS | HTML_EXTENSIONS
)


def ensure_dirs() -> None:
    """Create all required local directories if they don't already exist."""
    for directory in (
        ORIGINALS_DIR,
        PROCESSING_DIR,
        FAILED_DIR,
        CHROMA_PERSIST_DIR,
        SQLITE_DB_PATH.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)

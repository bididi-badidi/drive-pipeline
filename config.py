"""
config.py — centralised settings loaded from environment / .env file.
All other modules import from here; nothing reads os.environ directly.
"""

import hashlib
import os
import re
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
CHROMA_PERSIST_DIR: Path = _expand(os.getenv("CHROMA_PERSIST_DIR"), "~/.drive-pipeline/chroma")
CHROMA_COLLECTION_NAME: str | None = os.getenv("CHROMA_COLLECTION_NAME")
SQLITE_DB_PATH: Path = _expand(os.getenv("SQLITE_DB_PATH"), "~/.drive-pipeline/jobs.db")

# ── Google Drive archive ──────────────────────────────────────────────────────
DRIVE_ARCHIVE_ENABLED: bool = os.getenv("DRIVE_ARCHIVE_ENABLED", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
GOOGLE_DRIVE_CREDENTIALS_PATH: Path = _expand(
    os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH"),
    "~/.drive-pipeline/google-drive-credentials.json",
)
GOOGLE_DRIVE_TOKEN_PATH: Path = _expand(
    os.getenv("GOOGLE_DRIVE_TOKEN_PATH"),
    "~/.drive-pipeline/google-drive-token.json",
)
GOOGLE_DRIVE_ROOT_FOLDER_ID: str | None = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID") or None
GOOGLE_DRIVE_ARCHIVE_ROOT_NAME: str = os.getenv(
    "GOOGLE_DRIVE_ARCHIVE_ROOT_NAME",
    "drive-pipeline archive",
)

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 512  # target tokens per chunk
CHUNK_OVERLAP: int = 64  # overlap tokens between adjacent chunks

# ── Model IDs ─────────────────────────────────────────────────────────────────
MODEL_CACHE_DIR: Path = _expand(os.getenv("MODEL_CACHE_DIR"), "~/.drive-pipeline/models")
EMBEDDING_MODEL: str = "BAAI/bge-m3"  # local sentence-transformers model
VISION_MODEL: str = "models/gemini-2.5-flash"


def chroma_collection_name() -> str:
    """
    Return the Chroma collection for the configured embedding model.

    Chroma collections are dimension-locked after their first insert. Including
    the model name avoids mixing embeddings when EMBEDDING_MODEL changes.
    """
    if CHROMA_COLLECTION_NAME:
        return CHROMA_COLLECTION_NAME

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", EMBEDDING_MODEL).strip("_-").lower()
    digest = hashlib.sha1(EMBEDDING_MODEL.encode("utf-8")).hexdigest()[:8]
    prefix = "drive_pipeline"
    max_slug_length = 63 - len(prefix) - len(digest) - 2
    slug = slug[:max_slug_length].rstrip("_-")
    return f"{prefix}_{slug}_{digest}"


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

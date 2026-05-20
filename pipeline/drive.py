"""
pipeline/drive.py — optional Google Drive archival.

The worker calls this after text extraction and before local cleanup when
DRIVE_ARCHIVE_ENABLED=true. It keeps the local pipeline usable without Drive
credentials, while allowing v2 deployments to preserve originals in Drive.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

_service: Any | None = None


@dataclass(frozen=True)
class DriveArchiveResult:
    file_id: str
    web_view_link: str | None
    folder_id: str
    folder_path: str


def archive_file(path: Path, source_type: str | None) -> DriveArchiveResult | None:
    """Upload a file into the configured Drive archive folder tree."""
    if not config.DRIVE_ARCHIVE_ENABLED:
        return None

    service = _get_service()
    now = datetime.now(timezone.utc)
    folder_path_parts = [
        config.GOOGLE_DRIVE_ARCHIVE_ROOT_NAME,
        _folder_segment(source_type or "unknown"),
        f"{now.year:04d}",
        f"{now.month:02d}",
    ]
    folder_id = _ensure_folder_path(service, folder_path_parts)

    media = MediaFileUpload(str(path), resumable=True)
    request = service.files().create(
        body={"name": path.name, "parents": [folder_id]},
        media_body=media,
        fields="id, webViewLink",
    )
    result = request.execute()
    return DriveArchiveResult(
        file_id=result["id"],
        web_view_link=result.get("webViewLink"),
        folder_id=folder_id,
        folder_path="/".join(folder_path_parts),
    )


def _get_service() -> Any:
    global _service
    if _service is not None:
        return _service

    creds = _load_credentials()
    _service = build("drive", "v3", credentials=creds)
    return _service


def _load_credentials() -> Credentials:
    creds: Credentials | None = None
    token_path = config.GOOGLE_DRIVE_TOKEN_PATH

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        credentials_path = config.GOOGLE_DRIVE_CREDENTIALS_PATH
        if not credentials_path.exists():
            raise FileNotFoundError(
                "Google Drive archive is enabled, but credentials file was not found: "
                f"{credentials_path}"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    return creds


def _ensure_folder_path(service: Any, parts: list[str]) -> str:
    if config.GOOGLE_DRIVE_ROOT_FOLDER_ID:
        parent_id = config.GOOGLE_DRIVE_ROOT_FOLDER_ID
        parts_to_create = parts[1:]
    else:
        parent_id = None
        parts_to_create = parts

    for name in parts_to_create:
        parent_id = _find_or_create_folder(service, name, parent_id)
    if parent_id is None:
        raise RuntimeError("Could not resolve Google Drive archive folder")
    return parent_id


def _find_or_create_folder(service: Any, name: str, parent_id: str | None) -> str:
    existing = _find_folder(service, name, parent_id)
    if existing:
        return existing

    body: dict[str, Any] = {"name": name, "mimeType": FOLDER_MIME_TYPE}
    if parent_id:
        body["parents"] = [parent_id]

    result = service.files().create(body=body, fields="id").execute()
    return result["id"]


def _find_folder(service: Any, name: str, parent_id: str | None) -> str | None:
    query_parts = [
        f"name = '{_escape_query_value(name)}'",
        f"mimeType = '{FOLDER_MIME_TYPE}'",
        "trashed = false",
    ]
    if parent_id:
        query_parts.append(f"'{parent_id}' in parents")

    result = (
        service.files()
        .list(
            q=" and ".join(query_parts),
            spaces="drive",
            fields="files(id)",
            pageSize=1,
        )
        .execute()
    )
    files = result.get("files", [])
    return files[0]["id"] if files else None


def _escape_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _folder_segment(value: str) -> str:
    cleaned = value.strip().lower().replace("/", "-")
    return cleaned or "unknown"

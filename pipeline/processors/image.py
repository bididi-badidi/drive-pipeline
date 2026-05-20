"""
pipeline/processors/image.py — OCR via Gemini Vision.
"""

from pathlib import Path

from google import genai
from google.genai import types

import config

_PROMPT = (
    "Extract all text visible in this image. "
    "Return only the extracted text, preserving layout as much as possible. "
    "If there is no readable text, return an empty string."
)


def extract(path: Path) -> str:
    client = genai.Client(api_key=config.GOOGLE_API_KEY)

    image_data = path.read_bytes()
    mime = _mime_for(path.suffix.lower())

    response = client.models.generate_content(
        model=config.VISION_MODEL,
        contents=[
            types.Part.from_bytes(data=image_data, mime_type=mime),
            _PROMPT,
        ],
    )
    return response.text or ""


def _mime_for(suffix: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/jpeg")

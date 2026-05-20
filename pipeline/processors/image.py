"""
pipeline/processors/image.py — OCR via Gemini Vision.
"""

from pathlib import Path

import google.generativeai as genai

import config

_PROMPT = (
    "Extract all text visible in this image. "
    "Return only the extracted text, preserving layout as much as possible. "
    "If there is no readable text, return an empty string."
)


def extract(path: Path) -> str:
    genai.configure(api_key=config.GOOGLE_API_KEY)
    model = genai.GenerativeModel(config.VISION_MODEL)

    image_data = path.read_bytes()
    mime = _mime_for(path.suffix.lower())

    response = model.generate_content(
        [{"mime_type": mime, "data": image_data}, _PROMPT]
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

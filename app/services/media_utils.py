from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.schemas import MediaAsset


IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "avif"}
VIDEO_EXTENSIONS = {"mp4", "mov", "webm", "m4v", "mkv"}
AUDIO_EXTENSIONS = {"mp3", "m4a", "aac", "ogg", "opus", "wav"}
ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def clean_ext(value: str | None) -> str | None:
    if not value:
        return None
    return value.lower().lstrip(".")


def ext_from_url(url: str | None) -> str | None:
    if not url:
        return None
    path = Path(urlparse(url).path)
    return clean_ext(path.suffix)


def short_text(value: str | None, limit: int = 220) -> str | None:
    if not value:
        return None
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def strip_ansi(value: str | None) -> str | None:
    if value is None:
        return None
    return ANSI_ESCAPE_RE.sub("", value)


def best_thumbnail(entry: dict[str, Any]) -> str | None:
    thumbnails = entry.get("thumbnails") or []
    if thumbnails:
        best = thumbnails[-1]
        if isinstance(best, dict):
            return best.get("url")
    return entry.get("thumbnail")


def guess_asset_type(url: str | None, ext: str | None, *, has_duration: bool = False) -> str:
    ext = clean_ext(ext) or ext_from_url(url)
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if has_duration:
        return "video"
    return "unknown"


def collection_type(items: list[MediaAsset]) -> str:
    if not items:
        return "unknown"
    if len(items) == 1:
        return items[0].type
    item_types = {item.type for item in items}
    if item_types.issubset({"image", "video"}):
        return "carousel"
    if len(item_types) == 1:
        return "gallery"
    return "mixed"


def format_quality_label(fmt: dict[str, Any] | None) -> str | None:
    if not fmt:
        return None

    parts: list[str] = []
    if fmt.get("format_note"):
        parts.append(str(fmt["format_note"]))
    if fmt.get("height"):
        parts.append(f'{fmt["height"]}p')
    if fmt.get("tbr"):
        parts.append(f'{int(fmt["tbr"])}kbps')
    return " ".join(parts) or None

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_existing_path(raw_value: str | None) -> Path | None:
    if not raw_value:
        return None
    candidate = Path(raw_value.strip().strip('"'))
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve() if candidate.exists() else None


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _discover_cookie_file(markers: tuple[str, ...], cookies_dir: Path) -> Path | None:
    if not cookies_dir.exists():
        return None

    for path in sorted(cookies_dir.glob("*.txt")):
        content = _read_text_safe(path).lower()
        if any(marker in content for marker in markers):
            return path.resolve()
    for path in sorted(cookies_dir.glob("*.json")):
        content = _read_text_safe(path).lower()
        if any(marker in content for marker in markers):
            return path.resolve()
    return None


@dataclass(frozen=True)
class Settings:
    app_name: str
    debug: bool
    request_timeout_seconds: float
    tiktok_api_base: str
    cookies_dir: Path
    default_cookie_file: Path | None
    youtube_cookie_file: Path | None
    instagram_cookie_file: Path | None
    tiktok_cookie_file: Path | None
    instagram_sessionfile: str | None
    user_agent: str

    def cookie_file_for_provider(self, provider: str) -> Path | None:
        provider = provider.lower()
        if provider == "youtube":
            return self.youtube_cookie_file or self.default_cookie_file
        if provider == "instagram":
            return self.instagram_cookie_file or self.default_cookie_file
        if provider == "tiktok":
            return self.tiktok_cookie_file or self.default_cookie_file
        return self.default_cookie_file

    def cookie_file_for_url(self, url: str) -> Path | None:
        hostname = (urlparse(url).hostname or "").lower()
        if "youtube" in hostname or "youtu.be" in hostname or "google.com" in hostname:
            return self.cookie_file_for_provider("youtube")
        if "instagram" in hostname or "instagr.am" in hostname:
            return self.cookie_file_for_provider("instagram")
        if "tiktok" in hostname:
            return self.cookie_file_for_provider("tiktok")
        return self.default_cookie_file


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cookies_dir = _resolve_existing_path(os.getenv("COOKIES_DIR")) or (PROJECT_ROOT / "cookies")
    return Settings(
        app_name=os.getenv("APP_NAME", "Smart Media Extractor API"),
        debug=_as_bool(os.getenv("DEBUG"), default=False),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
        tiktok_api_base=os.getenv("TIKTOK_API_BASE", "https://www.tikwm.com/api/"),
        cookies_dir=cookies_dir,
        default_cookie_file=_resolve_existing_path(os.getenv("DEFAULT_COOKIE_FILE"))
        or _resolve_existing_path(os.getenv("COOKIE_FILE"))
        or _discover_cookie_file(("youtube.com", "instagram.com", "tiktok.com"), cookies_dir),
        youtube_cookie_file=_resolve_existing_path(os.getenv("YOUTUBE_COOKIE_FILE"))
        or _discover_cookie_file(("youtube.com", "youtu.be", "google.com", "accounts.google.com"), cookies_dir),
        instagram_cookie_file=_resolve_existing_path(os.getenv("INSTAGRAM_COOKIE_FILE"))
        or _discover_cookie_file(("instagram.com",), cookies_dir),
        tiktok_cookie_file=_resolve_existing_path(os.getenv("TIKTOK_COOKIE_FILE"))
        or _discover_cookie_file(("tiktok.com",), cookies_dir),
        instagram_sessionfile=os.getenv("INSTAGRAM_SESSIONFILE") or None,
        user_agent=os.getenv(
            "HTTP_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        ),
    )

from __future__ import annotations

import asyncio
import traceback
from abc import ABC
from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL

from app.config import get_settings
from app.logging_config import get_error_logger
from app.schemas import AudioFormat, ExtractResponse, ExtractorAttempt, MediaAsset, SubtitleTrack, VideoFormat
from app.services.errors import ExtractorError
from app.services.media_utils import best_thumbnail, clean_ext, collection_type, format_quality_label, guess_asset_type, strip_ansi

error_logger = get_error_logger()


class BaseExtractor(ABC):
    name = "base"

    async def extract(self, url: str, include_raw: bool = False) -> ExtractResponse:
        raise NotImplementedError


class _SilentYtDlpLogger:
    def debug(self, _: str) -> None:
        return

    def info(self, _: str) -> None:
        return

    def warning(self, _: str) -> None:
        return

    def error(self, _: str) -> None:
        return


def _sort_formats(formats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def score(fmt: dict[str, Any]) -> tuple[int, int, int, int]:
        return (
            int(fmt.get("height") or 0),
            int(fmt.get("width") or 0),
            int(fmt.get("tbr") or 0),
            int(fmt.get("filesize") or fmt.get("filesize_approx") or 0),
        )

    return sorted(formats, key=score, reverse=True)


def _pick_best_progressive(formats: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        fmt
        for fmt in formats
        if fmt.get("url") and fmt.get("vcodec") not in {None, "none"} and fmt.get("acodec") not in {None, "none"}
    ]
    return _sort_formats(candidates)[0] if candidates else None


def _pick_best_video_only(formats: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        fmt
        for fmt in formats
        if fmt.get("url") and fmt.get("vcodec") not in {None, "none"} and fmt.get("acodec") in {None, "none"}
    ]
    return _sort_formats(candidates)[0] if candidates else None


def _pick_best_audio_only(formats: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        fmt
        for fmt in formats
        if fmt.get("url") and fmt.get("acodec") not in {None, "none"} and fmt.get("vcodec") in {None, "none"}
    ]
    return _sort_formats(candidates)[0] if candidates else None


def normalize_yt_dlp_entry(entry: dict[str, Any], provider: str, position: int) -> MediaAsset | None:
    formats = [fmt for fmt in (entry.get("formats") or []) if isinstance(fmt, dict)]
    progressive = _pick_best_progressive(formats)
    video_only = _pick_best_video_only(formats)
    audio_only = _pick_best_audio_only(formats)

    selected = progressive or video_only
    url = (selected or audio_only or {}).get("url") or entry.get("url")
    ext = clean_ext((selected or audio_only or {}).get("ext")) or clean_ext(entry.get("ext"))
    asset_type = guess_asset_type(url, ext, has_duration=bool(entry.get("duration")))

    if not url:
        thumbnail = best_thumbnail(entry)
        if thumbnail:
            url = thumbnail
            asset_type = "image"
        else:
            return None

    return MediaAsset(
        id=str(entry.get("id") or position),
        type=asset_type,  # type: ignore[arg-type]
        url=url,
        thumbnail_url=best_thumbnail(entry),
        audio_url=None if progressive else (audio_only or {}).get("url"),
        width=(selected or {}).get("width") or entry.get("width"),
        height=(selected or {}).get("height") or entry.get("height"),
        duration_seconds=entry.get("duration"),
        ext=ext,
        size_bytes=(selected or audio_only or {}).get("filesize")
        or (selected or audio_only or {}).get("filesize_approx"),
        position=position,
        quality_label=format_quality_label(selected or audio_only),
        watermark=None,
        source=provider,
    )


class YtDlpBaseExtractor(BaseExtractor):
    name = "yt-dlp"

    async def extract(self, url: str, include_raw: bool = False) -> ExtractResponse:
        # yt-dlp sync ishlaydi, shuning uchun event loop ni bloklamaslik uchun thread ga o'tkaziladi.
        return await asyncio.to_thread(self._extract_sync, url, include_raw)

    def _extract_sync(self, url: str, include_raw: bool = False) -> ExtractResponse:
        settings = get_settings()
        cookie_file = settings.cookie_file_for_url(url)
        options = {
            "quiet": True,
            "skip_download": True,
            "no_warnings": True,
            "extract_flat": False,
            "noplaylist": False,
            "format": "all",
            "http_headers": {"User-Agent": settings.user_agent},
            "logger": _SilentYtDlpLogger(),
        }
        if cookie_file:
            # Platformaga mos cookies.txt berilsa, yt-dlp anti-bot/login wall holatlarini yaxshi yengadi.
            options["cookiefile"] = str(cookie_file)

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                data = ydl.sanitize_info(info)
        except Exception as exc:  # pragma: no cover - network/runtime branch
            cleaned_error = strip_ansi(str(exc)) or "Unknown yt-dlp error"
            cleaned_traceback = strip_ansi(traceback.format_exc()) or cleaned_error
            error_logger.error(
                'yt-dlp extraction failed | url="%s" | cookie_file="%s" | error="%s"\n%s',
                url,
                str(cookie_file) if cookie_file else "",
                cleaned_error,
                cleaned_traceback,
            )
            raise ExtractorError(
                f"yt-dlp extract_info xatosi: {cleaned_error}",
                provider=self.name,
                attempts=[ExtractorAttempt(provider=self.name, success=False, error=cleaned_error)],
            ) from exc

        entries = data.get("entries") or []
        items: list[MediaAsset] = []
        if entries:
            for index, entry in enumerate(entries, start=1):
                if not isinstance(entry, dict):
                    continue
                asset = normalize_yt_dlp_entry(entry, self.name, index)
                if asset:
                    items.append(asset)
        else:
            asset = normalize_yt_dlp_entry(data, self.name, 1)
            if asset:
                items.append(asset)

        if not items:
            raise ExtractorError(
                "yt-dlp media item topmadi",
                provider=self.name,
                attempts=[ExtractorAttempt(provider=self.name, success=False, error="No media items found.")],
            )

        source_provider = _infer_provider_name(data, url)
        request_headers = {
            "User-Agent": settings.user_agent,
            "Referer": _referer_for_provider(source_provider, data.get("webpage_url") or url),
        }

        return ExtractResponse(
            url=url,
            normalized_url=data.get("webpage_url") or data.get("original_url") or url,
            route="generic",
            provider=self.name,
            source_provider=source_provider,
            media_type=collection_type(items),  # type: ignore[arg-type]
            title=data.get("title"),
            description=data.get("description"),
            thumbnail_url=best_thumbnail(data),
            uploader=data.get("uploader") or data.get("channel") or data.get("uploader_id"),
            webpage_url=data.get("webpage_url") or url,
            duration_seconds=data.get("duration"),
            request_headers=request_headers,
            expires_at=_extract_expires_at(data, items),
            video_formats=_collect_video_formats(data),
            audio_formats=_collect_audio_formats(data),
            image_urls=_collect_image_urls(items),
            subtitle_tracks=_collect_subtitles(data),
            items=items,
            attempts=[ExtractorAttempt(provider=self.name, success=True)],
            raw=data if include_raw else None,
        )


def _collect_video_formats(data: dict[str, Any]) -> list[VideoFormat]:
    formats = []
    for fmt in data.get("formats") or []:
        if not isinstance(fmt, dict):
            continue
        if not fmt.get("url"):
            continue
        if clean_ext(fmt.get("ext")) != "mp4":
            continue
        if fmt.get("vcodec") in {None, "none"}:
            continue
        formats.append(
            VideoFormat(
                quality=format_quality_label(fmt) or "source",
                url=fmt["url"],
                size_bytes=fmt.get("filesize") or fmt.get("filesize_approx"),
                extension="mp4",
                has_audio=fmt.get("acodec") not in {None, "none"},
            )
        )
    return sorted(formats, key=lambda item: _quality_score(item.quality), reverse=True)


def _collect_audio_formats(data: dict[str, Any]) -> list[AudioFormat]:
    formats = []
    for fmt in data.get("formats") or []:
        if not isinstance(fmt, dict):
            continue
        if not fmt.get("url"):
            continue
        if fmt.get("acodec") in {None, "none"} or fmt.get("vcodec") not in {None, "none"}:
            continue
        ext = clean_ext(fmt.get("ext")) or "m4a"
        formats.append(
            AudioFormat(
                quality=format_quality_label(fmt) or "audio",
                url=fmt["url"],
                ext=ext,
                size_bytes=fmt.get("filesize") or fmt.get("filesize_approx"),
            )
        )
    return sorted(formats, key=lambda item: _quality_score(item.quality), reverse=True)


def _collect_subtitles(data: dict[str, Any]) -> list[SubtitleTrack]:
    tracks: list[SubtitleTrack] = []
    seen: set[tuple[str, str]] = set()

    # Manual subtitles ustun, automatic captions fallback sifatida qo'shiladi.
    subtitle_sources = [data.get("subtitles") or {}, data.get("automatic_captions") or {}]
    for source in subtitle_sources:
        for lang_code, entries in source.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict) or not entry.get("url"):
                    continue
                key = (lang_code, entry["url"])
                if key in seen:
                    continue
                seen.add(key)
                tracks.append(
                    SubtitleTrack(
                        lang_code=lang_code,
                        language=str(entry.get("name") or lang_code),
                        url=entry["url"],
                        format=clean_ext(entry.get("ext")) or "vtt",
                    )
                )
    return tracks


def _collect_image_urls(items: list[MediaAsset]) -> list[str]:
    return [item.url for item in items if item.type == "image"]


def _extract_expires_at(data: dict[str, Any], items: list[MediaAsset]) -> int | None:
    candidate_urls = [
        data.get("url"),
        data.get("webpage_url"),
        *[item.url for item in items],
        *[fmt.url for fmt in _collect_video_formats(data)],
        *[fmt.url for fmt in _collect_audio_formats(data)],
    ]
    for candidate in candidate_urls:
        if not candidate:
            continue
        parsed = urlparse(candidate)
        query = parse_qs(parsed.query)
        for key in ("expire", "expires", "Expires", "exp"):
            values = query.get(key)
            if not values:
                continue
            try:
                return int(float(values[0]))
            except (TypeError, ValueError):
                continue
    return None


def _infer_provider_name(data: dict[str, Any], fallback_url: str) -> str:
    extractor_key = str(data.get("extractor_key") or data.get("extractor") or "").lower()
    if "youtube" in extractor_key or "youtu" in extractor_key:
        return "youtube"
    if "instagram" in extractor_key or "insta" in extractor_key:
        return "instagram"
    if "tiktok" in extractor_key:
        return "tiktok"

    hostname = urlparse(data.get("webpage_url") or fallback_url).hostname or ""
    lowered_host = hostname.lower()
    if "youtube" in lowered_host or "youtu.be" in lowered_host:
        return "youtube"
    if "instagram" in lowered_host or "instagr.am" in lowered_host:
        return "instagram"
    if "tiktok" in lowered_host:
        return "tiktok"
    if lowered_host:
        return lowered_host.split(".")[-2] if "." in lowered_host else lowered_host
    return "generic"


def _referer_for_provider(provider: str, webpage_url: str) -> str:
    if provider == "youtube":
        return "https://www.youtube.com/"
    if provider == "instagram":
        return "https://www.instagram.com/"
    if provider == "tiktok":
        return "https://www.tiktok.com/"
    parsed = urlparse(webpage_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/"
    return webpage_url


def _quality_score(quality: str) -> int:
    numbers = "".join(character for character in quality if character.isdigit())
    if not numbers:
        return 0
    try:
        return int(numbers)
    except ValueError:
        return 0

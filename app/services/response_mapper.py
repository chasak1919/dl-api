from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from app.config import get_settings
from app.schemas import (
    ExtractResponse,
    StandardizedConfig,
    StandardizedExtractResponse,
    StandardizedMedia,
    StandardizedMetadata,
)
from app.services.media_utils import short_text


PLATFORM_REFERERS = {
    "youtube": "https://www.youtube.com/",
    "instagram": "https://www.instagram.com/",
    "tiktok": "https://www.tiktok.com/",
}


def map_extraction_result(result: ExtractResponse) -> StandardizedExtractResponse:
    # Ichki extractor natijasi tashqi API contractiga aynan bir xil ko'rinishda map qilinadi.
    provider = result.source_provider or "generic"
    metadata = StandardizedMetadata(
        title=result.title,
        author=result.uploader,
        duration=_format_duration(result.duration_seconds),
        thumbnail=result.thumbnail_url,
        description=short_text(result.description),
    )
    media = StandardizedMedia(
        video_mp4=result.video_formats,
        audio_only=result.audio_formats,
        images=result.image_urls,
        subtitles=result.subtitle_tracks,
    )
    config = StandardizedConfig(
        proxy_required=_proxy_required(result),
        headers=_headers_for_client(result),
        expires_at=result.expires_at or _guess_expires_at(result),
    )
    return StandardizedExtractResponse(
        provider=provider,
        metadata=metadata,
        media=media,
        config=config,
    )


def _format_duration(duration_seconds: float | None) -> str | None:
    if duration_seconds is None:
        return None
    total_seconds = int(duration_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return f"{minutes:02}:{seconds:02}"


def _headers_for_client(result: ExtractResponse) -> dict[str, str]:
    settings = get_settings()
    headers = {"User-Agent": settings.user_agent}
    referer = result.request_headers.get("Referer") or PLATFORM_REFERERS.get(result.source_provider)
    if referer:
        headers["Referer"] = referer
    return headers


def _proxy_required(result: ExtractResponse) -> bool:
    media_urls = [
        *[item.url for item in result.items],
        *[video.url for video in result.video_formats],
        *[audio.url for audio in result.audio_formats],
    ]
    sensitive_domains = ("tiktokcdn", "fbcdn", "cdninstagram", "googlevideo")
    signed_urls = ("expire=", "expires=", "signature=", "token=", "auth=")
    return result.source_provider in {"instagram", "tiktok"} or any(
        any(token in (url or "").lower() for token in signed_urls) or any(domain in (url or "").lower() for domain in sensitive_domains)
        for url in media_urls
    )


def _guess_expires_at(result: ExtractResponse) -> int | None:
    urls = [
        *[item.url for item in result.items],
        *[video.url for video in result.video_formats],
        *[audio.url for audio in result.audio_formats],
    ]
    for url in urls:
        parsed = urlparse(url)
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

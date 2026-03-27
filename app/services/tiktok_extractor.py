from __future__ import annotations

import httpx

from app.config import get_settings
from app.logging_config import get_error_logger
from app.schemas import AudioFormat, ExtractResponse, ExtractorAttempt, MediaAsset, VideoFormat
from app.services.errors import ExtractorError
from app.services.media_utils import collection_type, ext_from_url, short_text
from app.services.ytdlp_base import BaseExtractor

error_logger = get_error_logger()


class TikTokExtractor(BaseExtractor):
    name = "tiktok-special"

    async def extract(self, url: str, include_raw: bool = False) -> ExtractResponse:
        settings = get_settings()
        headers = {
            "User-Agent": settings.user_agent,
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.tikwm.com/",
        }

        # Watermarksiz link olish uchun maxsus provider avval ishlatiladi.
        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(settings.tiktok_api_base, params={"url": url})
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # pragma: no cover - runtime/network branch
            error_logger.exception('TikTok provider failed | url="%s"', url)
            raise ExtractorError(
                "TikTok custom provider ishlamadi",
                provider="tikwm",
                attempts=[ExtractorAttempt(provider="tikwm", success=False, error=str(exc))],
            ) from exc

        if payload.get("code") != 0 or not isinstance(payload.get("data"), dict):
            raise ExtractorError(
                "TikTok custom provider noto'g'ri javob qaytardi",
                provider="tikwm",
                attempts=[
                    ExtractorAttempt(
                        provider="tikwm",
                        success=False,
                        error=str(payload.get("msg") or "Unexpected TikWM response"),
                    )
                ],
                details=payload,
            )

        data = payload["data"]
        audio_url = None
        if isinstance(data.get("music_info"), dict):
            audio_url = data["music_info"].get("play")

        items: list[MediaAsset] = []
        if data.get("play"):
            items.append(
                MediaAsset(
                    id=str(data.get("id") or "1"),
                    type="video",
                    url=data["play"],
                    thumbnail_url=data.get("origin_cover") or data.get("cover"),
                    audio_url=audio_url,
                    duration_seconds=data.get("duration"),
                    ext=ext_from_url(data.get("play")),
                    size_bytes=data.get("size"),
                    position=1,
                    quality_label="no-watermark",
                    watermark=False,
                    source="tikwm",
                )
            )

        # Photo-mode TikTok postlari uchun rasmlar ham qaytariladi.
        if not items and isinstance(data.get("images"), list):
            for index, image_url in enumerate(data["images"], start=1):
                if not image_url:
                    continue
                items.append(
                    MediaAsset(
                        id=f'{data.get("id", "photo")}-{index}',
                        type="image",
                        url=image_url,
                        thumbnail_url=image_url,
                        ext=ext_from_url(image_url),
                        position=index,
                        source="tikwm",
                    )
                )

        if not items:
            raise ExtractorError(
                "TikTok media URL topilmadi",
                provider="tikwm",
                attempts=[ExtractorAttempt(provider="tikwm", success=False, error="Media URL topilmadi.")],
                details=payload,
            )

        return ExtractResponse(
            url=url,
            normalized_url=url,
            route="tiktok",
            provider="tikwm",
            source_provider="tiktok",
            media_type=collection_type(items),  # type: ignore[arg-type]
            title=data.get("title") or short_text(data.get("content_desc"), 120),
            description=short_text(data.get("content_desc")),
            thumbnail_url=data.get("origin_cover") or data.get("cover"),
            uploader=(data.get("author") or {}).get("unique_id") if isinstance(data.get("author"), dict) else None,
            webpage_url=url,
            duration_seconds=data.get("duration"),
            request_headers={
                "User-Agent": settings.user_agent,
                "Referer": "https://www.tiktok.com/",
            },
            video_formats=[
                VideoFormat(
                    quality=items[0].quality_label or "source",
                    url=items[0].url,
                    size_bytes=items[0].size_bytes,
                    extension=items[0].ext or "mp4",
                    has_audio=True,
                )
            ]
            if items and items[0].type == "video"
            else [],
            audio_formats=[
                AudioFormat(
                    quality="music",
                    url=audio_url,
                    ext=ext_from_url(audio_url) or "mp3",
                    size_bytes=None,
                )
            ]
            if audio_url
            else [],
            image_urls=[item.url for item in items if item.type == "image"],
            items=items,
            attempts=[ExtractorAttempt(provider="tikwm", success=True)],
            raw=payload if include_raw else None,
        )

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import instaloader

from app.config import get_settings
from app.logging_config import get_error_logger
from app.schemas import ExtractResponse, ExtractorAttempt, MediaAsset, VideoFormat
from app.services.errors import ExtractorError
from app.services.media_utils import collection_type, ext_from_url, guess_asset_type, short_text
from app.services.ytdlp_base import BaseExtractor

error_logger = get_error_logger()


def normalize_gallery_item(entry: dict[str, Any], provider: str, position: int) -> MediaAsset | None:
    url = entry.get("url")
    ext = entry.get("extension") or ext_from_url(url)
    if not url:
        return None
    asset_type = guess_asset_type(url, ext)
    return MediaAsset(
        id=str(entry.get("id") or entry.get("num") or position),
        type=asset_type,  # type: ignore[arg-type]
        url=url,
        thumbnail_url=url if asset_type == "image" else entry.get("display_url"),
        ext=ext_from_url(url),
        position=position,
        source=provider,
    )


class InstagramExtractor(BaseExtractor):
    name = "instagram-special"

    async def extract(self, url: str, include_raw: bool = False) -> ExtractResponse:
        attempts: list[ExtractorAttempt] = []

        # Avval Instagram uchun maxsus kutubxona sinab ko'riladi.
        try:
            result = await asyncio.to_thread(self._extract_with_instaloader, url, include_raw)
            result.attempts = [ExtractorAttempt(provider="instaloader", success=True)]
            return result
        except Exception as exc:
            error_logger.exception('Instagram instaloader failed | url="%s"', url)
            attempts.append(ExtractorAttempt(provider="instaloader", success=False, error=str(exc)))

        # Agar login wall yoki boshqa cheklov bo'lsa, gallery-dl ikkinchi fallback bo'ladi.
        try:
            result = await asyncio.to_thread(self._extract_with_gallery_dl, url, include_raw)
            result.attempts = [*attempts, ExtractorAttempt(provider="gallery-dl", success=True)]
            return result
        except Exception as exc:
            error_logger.exception('Instagram gallery-dl failed | url="%s"', url)
            attempts.append(ExtractorAttempt(provider="gallery-dl", success=False, error=str(exc)))

        raise ExtractorError(
            "Instagram uchun maxsus extractorlar ishlamadi",
            provider=self.name,
            attempts=attempts,
        )

    def _extract_with_instaloader(self, url: str, include_raw: bool = False) -> ExtractResponse:
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            raise ValueError("Instagram shortcode topilmadi.")

        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
        )
        self._configure_login(loader)

        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        caption = post.caption if isinstance(post.caption, str) else None
        items: list[MediaAsset] = []

        # Carousel bo'lsa, ichidagi barcha rasm/video elementlar qaytariladi.
        if post.typename == "GraphSidecar":
            for index, node in enumerate(post.get_sidecar_nodes(), start=1):
                node_url = node.video_url if node.is_video else node.display_url
                items.append(
                    MediaAsset(
                        id=f"{post.shortcode}-{index}",
                        type="video" if node.is_video else "image",
                        url=node_url,
                        thumbnail_url=node.display_url,
                        ext=ext_from_url(node_url),
                        position=index,
                        watermark=False if node.is_video else None,
                        source="instaloader",
                    )
                )
        else:
            node_url = post.video_url if post.is_video else post.url
            items.append(
                MediaAsset(
                    id=str(post.mediaid),
                    type="video" if post.is_video else "image",
                    url=node_url,
                    thumbnail_url=post.url,
                    duration_seconds=post.video_duration if post.is_video else None,
                    ext=ext_from_url(node_url),
                    position=1,
                    watermark=False if post.is_video else None,
                    source="instaloader",
                )
            )

        if not items:
            raise ValueError("Instaloader media item topmadi.")

        raw_payload = None
        if include_raw:
            raw_payload = {
                "shortcode": post.shortcode,
                "typename": post.typename,
                "caption": caption,
                "mediaid": str(post.mediaid),
            }

        return ExtractResponse(
            url=url,
            normalized_url=f"https://www.instagram.com/p/{post.shortcode}/",
            route="instagram",
            provider="instaloader",
            source_provider="instagram",
            media_type=collection_type(items),  # type: ignore[arg-type]
            title=short_text(caption, 120),
            description=short_text(caption),
            thumbnail_url=items[0].thumbnail_url,
            uploader=post.owner_username,
            webpage_url=f"https://www.instagram.com/p/{post.shortcode}/",
            duration_seconds=post.video_duration if post.is_video else None,
            request_headers={
                "User-Agent": get_settings().user_agent,
                "Referer": "https://www.instagram.com/",
            },
            video_formats=_build_video_formats(items),
            image_urls=[item.url for item in items if item.type == "image"],
            items=items,
            raw=raw_payload,
        )

    def _extract_with_gallery_dl(self, url: str, include_raw: bool = False) -> ExtractResponse:
        settings = get_settings()
        command = [sys.executable, "-m", "gallery_dl", "--dump-json", "--no-download"]
        if settings.instagram_cookie_file:
            # Agar Instagram cookies.txt bo'lsa, gallery-dl ham undan foydalansin.
            command.extend(["--cookies", str(settings.instagram_cookie_file)])
        command.append(url)
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if completed.returncode != 0:
            error_message = completed.stderr.strip() or completed.stdout.strip() or "gallery-dl exited with an error."
            raise RuntimeError(error_message)

        raw_entries: list[dict[str, Any]] = []
        for line in completed.stdout.splitlines():
            stripped = line.strip()
            if not stripped.startswith("{"):
                continue
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(decoded, dict) and decoded.get("url"):
                raw_entries.append(decoded)

        if not raw_entries:
            raise RuntimeError("gallery-dl structured output qaytarmadi.")

        items = [
            asset
            for index, entry in enumerate(raw_entries, start=1)
            if (asset := normalize_gallery_item(entry, "gallery-dl", index)) is not None
        ]

        if not items:
            raise RuntimeError("gallery-dl media item topmadi.")

        return ExtractResponse(
            url=url,
            normalized_url=url,
            route="instagram",
            provider="gallery-dl",
            source_provider="instagram",
            media_type=collection_type(items),  # type: ignore[arg-type]
            thumbnail_url=items[0].thumbnail_url,
            webpage_url=url,
            request_headers={
                "User-Agent": get_settings().user_agent,
                "Referer": "https://www.instagram.com/",
            },
            video_formats=_build_video_formats(items),
            image_urls=[item.url for item in items if item.type == "image"],
            items=items,
            raw=raw_entries if include_raw else None,
        )

    @staticmethod
    def _extract_shortcode(url: str) -> str | None:
        marker = urlparse(url).path.strip("/").split("/")
        if len(marker) >= 2 and marker[0] in {"p", "reel", "tv"}:
            return marker[1]
        return None

    @staticmethod
    def _configure_login(loader: instaloader.Instaloader) -> None:
        settings = get_settings()
        if settings.instagram_sessionfile:
            username = Path(settings.instagram_sessionfile).name.replace("session-", "")
            loader.load_session_from_file(username, settings.instagram_sessionfile)
        # Release flow login/parolga tayanmaydi; session bo'lmasa keyingi fallbacklar ishlaydi.


def _build_video_formats(items: list[MediaAsset]) -> list[VideoFormat]:
    return [
        VideoFormat(
            quality=item.quality_label or "source",
            url=item.url,
            size_bytes=item.size_bytes,
            extension=item.ext or "mp4",
            has_audio=True,
        )
        for item in items
        if item.type == "video"
    ]

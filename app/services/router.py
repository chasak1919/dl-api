from __future__ import annotations

import re
from urllib.parse import urlparse

from app.schemas import ExtractResponse, ExtractorAttempt
from app.services.errors import ExtractorError, classify_error_message
from app.services.instagram_extractor import InstagramExtractor
from app.services.tiktok_extractor import TikTokExtractor
from app.services.youtube_extractor import YoutubeExtractor


INSTAGRAM_RE = re.compile(r"https?://(?:www\.)?(?:instagram\.com|instagr\.am)/", re.IGNORECASE)
TIKTOK_RE = re.compile(r"https?://(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/", re.IGNORECASE)


class SmartRouter:
    def __init__(self) -> None:
        self._yt_dlp = YoutubeExtractor()
        self._instagram = InstagramExtractor()
        self._tiktok = TikTokExtractor()

    def detect_route(self, url: str) -> str:
        if INSTAGRAM_RE.search(url):
            return "instagram"
        if TIKTOK_RE.search(url):
            return "tiktok"
        return "generic"

    def detect_provider_label(self, url: str) -> str:
        hostname = (urlparse(url).hostname or "").lower()
        if "youtube" in hostname or "youtu.be" in hostname or "google.com" in hostname:
            return "youtube"
        if "instagram" in hostname or "instagr.am" in hostname:
            return "instagram"
        if "tiktok" in hostname:
            return "tiktok"
        return self.detect_route(url)

    async def extract(self, url: str, include_raw: bool = False) -> ExtractResponse:
        route = self.detect_route(url)
        attempt_log: list[ExtractorAttempt] = []

        chain = {
            "instagram": [self._instagram, self._yt_dlp],
            "tiktok": [self._tiktok, self._yt_dlp],
            "generic": [self._yt_dlp],
        }[route]

        errors: list[str] = []
        final_code = "extraction_failed"
        final_status = 422
        for extractor in chain:
            try:
                # Bir extractor yiqilsa, keyingi fallback avtomatik sinab ko'riladi.
                result = await extractor.extract(url, include_raw=include_raw)
                result.route = route  # type: ignore[assignment]
                result.attempts = [*attempt_log, *result.attempts]
                if not result.normalized_url:
                    result.normalized_url = result.webpage_url or url
                return result
            except ExtractorError as exc:
                attempt_log.extend(exc.attempts)
                errors.append(f"{extractor.name}: {exc}")
                combined_attempt_errors = " ".join(attempt.error or "" for attempt in attempt_log)
                final_code, final_status = classify_error_message(combined_attempt_errors or str(exc))

        raise ExtractorError(
            "Barcha extractorlar muvaffaqiyatsiz tugadi",
            provider=self.detect_provider_label(url),
            attempts=attempt_log or [
                ExtractorAttempt(provider=self.detect_provider_label(url), success=False, error="No extractor produced a result.")
            ],
            details={"errors": errors},
            code=final_code,
            http_status=final_status,
        )

from __future__ import annotations

from app.services.media_utils import short_text
from app.services.ytdlp_base import YtDlpBaseExtractor


class YoutubeExtractor(YtDlpBaseExtractor):
    name = "yt-dlp"

    async def extract(self, url: str, include_raw: bool = False):
        # Generic extractor barcha qo'llab-quvvatlangan saytlar uchun universal fallback bo'lib ishlaydi.
        result = await super().extract(url, include_raw=include_raw)
        result.title = short_text(result.title, 120)
        result.description = short_text(result.description)
        return result


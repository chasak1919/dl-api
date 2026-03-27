from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator

import httpx
from starlette.background import BackgroundTask

from app.config import get_settings
from app.logging_config import get_error_logger
from app.schemas import MediaAsset
from app.services.errors import StreamProxyError
from app.services.router import SmartRouter

error_logger = get_error_logger()


@dataclass
class StreamResult:
    iterator: AsyncIterator[bytes]
    media_type: str
    status_code: int
    headers: dict[str, str]
    background: BackgroundTask


class StreamProxyService:
    def __init__(self, router: SmartRouter) -> None:
        self._router = router

    async def open_stream(
        self,
        *,
        client: httpx.AsyncClient,
        source_url: str | None,
        media_url: str | None,
        item_index: int,
        include_raw: bool,
        referer: str | None,
        request_range: str | None,
    ) -> StreamResult:
        target_url = media_url
        effective_referer = referer

        # Agar media URL tashqi tomonda hotlink bilan himoyalangan bo'lsa, uni oldin extract qilib olamiz.
        if not target_url:
            if not source_url:
                raise StreamProxyError("Streaming uchun kamida 'url' yoki 'media_url' kerak.", http_status=422)
            extraction = await self._router.extract(source_url, include_raw=include_raw)
            asset = self._select_asset(extraction.items, item_index)
            target_url = asset.url
            effective_referer = effective_referer or extraction.webpage_url or source_url

        headers = {"User-Agent": get_settings().user_agent}
        if effective_referer:
            headers["Referer"] = effective_referer
        if request_range:
            headers["Range"] = request_range

        try:
            upstream_request = client.build_request("GET", target_url, headers=headers)
            upstream_response = await client.send(upstream_request, stream=True)
        except Exception as exc:  # pragma: no cover - network/runtime branch
            error_logger.exception('Stream proxy open failed | target_url="%s"', target_url)
            raise StreamProxyError("Media stream ochilmadi.", details={"reason": str(exc)}) from exc

        if upstream_response.status_code >= 400:
            await upstream_response.aclose()
            raise StreamProxyError(
                "Upstream media server stream berishni rad etdi.",
                details={"status_code": upstream_response.status_code, "target_url": target_url},
                http_status=upstream_response.status_code,
            )

        passthrough_headers = {}
        for header_name in ("content-length", "content-range", "accept-ranges", "etag", "last-modified"):
            if header_name in upstream_response.headers:
                passthrough_headers[header_name] = upstream_response.headers[header_name]

        media_type = upstream_response.headers.get("content-type", "application/octet-stream")
        return StreamResult(
            iterator=upstream_response.aiter_bytes(),
            media_type=media_type,
            status_code=upstream_response.status_code,
            headers=passthrough_headers,
            background=BackgroundTask(upstream_response.aclose),
        )

    @staticmethod
    def _select_asset(items: list[MediaAsset], item_index: int) -> MediaAsset:
        if not items:
            raise StreamProxyError("Streaming uchun media item topilmadi.", http_status=404)
        if item_index < 1 or item_index > len(items):
            raise StreamProxyError(
                "Berilgan item_index mavjud emas.",
                details={"available_items": len(items), "requested_item_index": item_index},
                http_status=404,
            )
        return items[item_index - 1]

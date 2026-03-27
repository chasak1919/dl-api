from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.schemas import ErrorResponse, ExtractorAttempt


def classify_error_message(message: str) -> tuple[str, int]:
    lowered = message.lower()

    # Private or login wall errors should surface as access-related failures.
    if any(
        keyword in lowered
        for keyword in (
            "private",
            "login",
            "sign in",
            "not authorized",
            "authentication",
            "cookie",
            "cookies-from-browser",
            "empty media response",
        )
    ):
        return "private_or_login_required", 403

    # Missing content should be clearly marked as not found.
    if any(
        keyword in lowered
        for keyword in (
            "not found",
            "deleted",
            "unavailable",
            "404",
            "does not exist",
            "no media items found",
            "media item topmadi",
        )
    ):
        return "media_not_found", 404

    # Rate limits, geo blocks, and IP restrictions are grouped together.
    if any(keyword in lowered for keyword in ("429", "rate limit", "too many requests")):
        return "rate_limited", 429
    if any(keyword in lowered for keyword in ("blocked", "forbidden", "geo", "ip", "access denied", "403")):
        return "access_blocked", 403

    if "timeout" in lowered:
        return "upstream_timeout", 504

    return "extraction_failed", 422


def public_error_message(code: str, provider: str | None = None) -> str:
    messages = {
        "private_or_login_required": "Media yopiq yoki login talab qilinadi.",
        "media_not_found": "Video topilmadi.",
        "rate_limited": "Juda ko'p urinish bo'ldi. Keyinroq qayta urinib ko'ring.",
        "access_blocked": "Kirish vaqtincha bloklandi.",
        "upstream_timeout": "So'rov vaqti tugadi. Keyinroq qayta urinib ko'ring.",
        "extraction_failed": "Media ajratishda xatolik yuz berdi.",
        "stream_proxy_failed": "Media stream ochilmadi.",
        "validation_error": "So'rov parametrlari noto'g'ri.",
        "internal_server_error": "Kutilmagan ichki xatolik yuz berdi.",
    }
    return messages.get(code, f"{provider or 'Media'} bo'yicha xatolik yuz berdi.")


class ExtractorError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        attempts: list[ExtractorAttempt] | None = None,
        details: dict[str, Any] | None = None,
        code: str | None = None,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        guessed_code, guessed_status = classify_error_message(message)
        self.provider = provider
        self.attempts = attempts or []
        self.details = details or {}
        self.code = code or guessed_code
        self.http_status = http_status or guessed_status


class StreamProxyError(RuntimeError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None, http_status: int = 502) -> None:
        super().__init__(message)
        self.details = details or {}
        self.http_status = http_status


def build_error_response(exc: ExtractorError | StreamProxyError) -> ErrorResponse:
    settings = get_settings()

    if isinstance(exc, ExtractorError):
        if settings.debug:
            return ErrorResponse(
                code=exc.code,
                message=str(exc),
                provider=exc.provider,
                attempts=exc.attempts,
                details=exc.details,
            )

        return ErrorResponse(
            code=exc.code,
            message=public_error_message(exc.code, exc.provider),
            provider=exc.provider,
            attempts=[],
            details={},
        )

    if settings.debug:
        return ErrorResponse(
            code="stream_proxy_failed",
            message=str(exc),
            details=exc.details,
        )

    return ErrorResponse(
        code="stream_proxy_failed",
        message=public_error_message("stream_proxy_failed"),
        details={},
    )

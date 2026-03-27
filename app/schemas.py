from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    url: str = Field(..., min_length=5)
    include_raw: bool = False


class ExtractorAttempt(BaseModel):
    provider: str
    success: bool
    error: str | None = None


class MediaAsset(BaseModel):
    id: str
    type: Literal["video", "image", "audio", "unknown"]
    url: str
    proxy_url: str | None = None
    thumbnail_url: str | None = None
    audio_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    ext: str | None = None
    size_bytes: int | None = None
    position: int | None = None
    quality_label: str | None = None
    watermark: bool | None = None
    source: str | None = None


class VideoFormat(BaseModel):
    quality: str
    url: str
    size_bytes: int | None = None
    extension: str
    has_audio: bool


class AudioFormat(BaseModel):
    quality: str
    url: str
    ext: str
    size_bytes: int | None = None


class SubtitleTrack(BaseModel):
    lang_code: str
    language: str
    url: str
    format: str


class ExtractResponse(BaseModel):
    status: Literal["success"] = "success"
    url: str
    normalized_url: str
    route: Literal["instagram", "tiktok", "generic"]
    provider: str
    source_provider: str = "generic"
    media_type: Literal["video", "image", "audio", "carousel", "gallery", "mixed", "unknown"]
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    uploader: str | None = None
    webpage_url: str | None = None
    duration_seconds: float | None = None
    request_headers: dict[str, str] = Field(default_factory=dict)
    expires_at: int | None = None
    video_formats: list[VideoFormat] = Field(default_factory=list)
    audio_formats: list[AudioFormat] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    subtitle_tracks: list[SubtitleTrack] = Field(default_factory=list)
    items: list[MediaAsset] = Field(default_factory=list)
    attempts: list[ExtractorAttempt] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw: dict[str, Any] | list[dict[str, Any]] | None = None


class StreamRequest(BaseModel):
    url: str | None = Field(default=None, min_length=5)
    media_url: str | None = Field(default=None, min_length=5)
    item_index: int = Field(default=1, ge=1)
    include_raw: bool = False
    referer: str | None = None


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    code: str
    message: str
    provider: str | None = None
    attempts: list[ExtractorAttempt] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class StandardizedMetadata(BaseModel):
    title: str | None = None
    author: str | None = None
    duration: str | None = None
    thumbnail: str | None = None
    description: str | None = None


class StandardizedMedia(BaseModel):
    video_mp4: list[VideoFormat] = Field(default_factory=list)
    audio_only: list[AudioFormat] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    subtitles: list[SubtitleTrack] = Field(default_factory=list)


class StandardizedConfig(BaseModel):
    proxy_required: bool
    headers: dict[str, str] = Field(default_factory=dict)
    expires_at: int | None = None


class StandardizedExtractResponse(BaseModel):
    status: Literal["success"] = "success"
    provider: str
    metadata: StandardizedMetadata
    media: StandardizedMedia
    config: StandardizedConfig

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal


ProgressCallback = Callable[[str], None]


@dataclass
class Post:
    row_number: int
    title: str
    content: str
    featured_image_url: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    status: str = "draft"
    publish_date: str | None = None
    ma_bai: str | None = None


@dataclass
class UploadedMedia:
    media_id: int
    source_url: str
    filename: str | None = None


@dataclass
class MatchedImages:
    background: Path | None = None
    content_images: list[Path] = field(default_factory=list)


PostStatus = Literal["success", "failed", "skipped"]


@dataclass
class PostResult:
    row_number: int
    title: str
    status: PostStatus
    link: str | None = None
    error: str | None = None


@dataclass
class WordPressConfig:
    site_url: str
    username: str
    application_password: str
    timeout_seconds: int = 30
    retry_count: int = 3
    delay_seconds: float = 0.0


@dataclass
class PosterOptions:
    max_images_per_post: int = 5
    default_status: str = "draft"
    skip_duplicates: bool = True
    dry_run: bool = False

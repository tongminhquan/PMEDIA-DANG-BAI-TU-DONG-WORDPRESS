from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Post

REQUIRED_COLUMNS = {"title", "content"}
OPTIONAL_COLUMNS = {"featured_image_url", "category", "tags", "status", "publish_date", "ma_bai"}


class ExcelValidationError(ValueError):
    pass


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _parse_tags(value: Any) -> list[str]:
    text = _clean(value)
    if not text:
        return []
    return [tag.strip() for tag in text.split(",") if tag.strip()]


def read_posts_from_excel(excel_path: str | Path, default_status: str = "draft") -> list[Post]:
    """Read and validate posts from an Excel workbook."""

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("pandas and openpyxl are required to read Excel files") from exc

    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file does not exist: {path}")

    try:
        frame = pd.read_excel(path)
    except Exception as exc:
        raise ExcelValidationError(f"Cannot read Excel file: {exc}") from exc

    columns = {str(column).strip() for column in frame.columns}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ExcelValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

    posts: list[Post] = []
    for index, row in frame.iterrows():
        title = _clean(row.get("title"))
        content = _clean(row.get("content"))
        if not title or not content:
            raise ExcelValidationError(f"Row {index + 2} must include title and content")

        posts.append(
            Post(
                row_number=index + 2,
                title=title,
                content=content,
                featured_image_url=_clean(row.get("featured_image_url")),
                category=_clean(row.get("category")),
                tags=_parse_tags(row.get("tags")),
                status=_clean(row.get("status")) or default_status,
                publish_date=_clean(row.get("publish_date")),
                ma_bai=_clean(row.get("ma_bai")),
            )
        )

    return posts

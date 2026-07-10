from __future__ import annotations

from pathlib import Path
import re
import unicodedata
from typing import Any

from .models import Post, PostUpdate

REQUIRED_COLUMNS = {"title", "content"}
UPDATE_IDENTIFIER_COLUMNS = {"post_id", "link", "slug", "ma_bai", "title"}
OPTIONAL_COLUMNS = {
    "featured_image_url",
    "category",
    "tags",
    "status",
    "publish_date",
    "ma_bai",
    "slug",
    "meta_description",
}

COLUMN_ALIASES = {
    "title": {"title", "post title", "tieu de", "tieu de seo"},
    "content": {"content", "noi dung", "noi dung html", "noi dung html thuan"},
    "featured_image_url": {"featured image url", "featured_image_url", "anh dai dien", "url anh dai dien"},
    "category": {"category", "danh muc"},
    "tags": {"tags", "tag", "the", "the wordpress", "wordpress tags"},
    "primary_keyword": {"tu khoa chinh", "keyword chinh", "main keyword"},
    "secondary_keywords": {"tu khoa phu", "tu khoa phu da phu them", "secondary keywords"},
    "status": {"status", "trang thai"},
    "publish_date": {"publish date", "publish_date", "ngay dang", "lich dang"},
    "ma_bai": {"ma bai", "ma_bai", "id bai", "code"},
    "post_id": {"post id", "post_id", "id bai viet", "id wordpress", "wordpress id", "wp id", "id"},
    "link": {"link bai viet", "link", "url bai viet"},
    "slug": {"slug", "duong dan", "duong dan tinh"},
    "seo_title": {"seo title", "tieu de seo", "rank math title"},
    "meta_description": {"meta description", "mo ta", "mo ta meta", "mo ta meta seo", "meta seo"},
}


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


def _parse_keywords(value: Any) -> list[str]:
    text = _clean(value)
    if not text:
        return []
    return _dedupe(
        [keyword.strip() for keyword in re.split(r"[,;|\r\n]+", text) if keyword.strip()]
    )


def read_posts_from_excel(
    excel_path: str | Path,
    default_status: str = "draft",
    sheet_name: str | int | None = None,
) -> list[Post]:
    """Read and validate posts from an Excel workbook."""

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("pandas and openpyxl are required to read Excel files") from exc

    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file does not exist: {path}")

    frame, column_map = _read_best_sheet(pd, path, sheet_name)

    missing = REQUIRED_COLUMNS - set(column_map)
    if missing:
        raise ExcelValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

    posts: list[Post] = []
    for index, row in frame.iterrows():
        if row.isna().all():
            continue

        title = _clean(row.get(column_map["title"]))
        content = _clean(row.get(column_map["content"]))
        if not title or not content:
            raise ExcelValidationError(f"Row {index + 2} must include title and content")

        tags = _parse_tags(row.get(column_map.get("tags")))
        primary_values = _parse_keywords(row.get(column_map.get("primary_keyword")))
        primary_keyword = primary_values[0] if primary_values else None
        secondary_keywords = _dedupe(
            [
                *primary_values[1:],
                *_parse_keywords(row.get(column_map.get("secondary_keywords"))),
            ]
        )

        # Build focus_keywords from primary + secondary keywords
        focus_parts: list[str] = []
        if primary_keyword:
            focus_parts.append(primary_keyword)
        focus_parts.extend(secondary_keywords)
        focus_keywords = _dedupe(focus_parts)

        slug = _clean(row.get(column_map.get("slug")))
        ma_bai = _clean(row.get(column_map.get("ma_bai"))) or _post_code_from_slug(slug)

        posts.append(
            Post(
                row_number=index + 2,
                title=title,
                content=content,
                featured_image_url=_clean(row.get(column_map.get("featured_image_url"))),
                category=_clean(row.get(column_map.get("category"))),
                tags=tags,
                status=_clean(row.get(column_map.get("status"))) or default_status,
                publish_date=_clean(row.get(column_map.get("publish_date"))),
                ma_bai=ma_bai,
                slug=slug,
                seo_title=_clean(row.get(column_map.get("seo_title"))) or title,
                meta_description=_clean(row.get(column_map.get("meta_description"))),
                focus_keywords=focus_keywords,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
            )
        )

    return posts


def read_post_updates_from_excel(
    excel_path: str | Path,
    sheet_name: str | int | None = None,
) -> list[PostUpdate]:
    """Read partial post updates from Excel; only non-empty cells become fields.

    Rows are matched to website posts later by ID, link/slug or title, so the
    workbook only needs at least one of those identifier columns.
    """

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("pandas and openpyxl are required to read Excel files") from exc

    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file does not exist: {path}")

    frame, column_map = _read_update_sheet(pd, path, sheet_name)

    updates: list[PostUpdate] = []
    for index, row in frame.iterrows():
        if row.isna().all():
            continue

        post_id = _parse_post_id(row.get(column_map.get("post_id")))
        link = _clean(row.get(column_map.get("link")))
        slug = _clean(row.get(column_map.get("slug")))
        title = _clean(row.get(column_map.get("title")))
        if post_id is None and not link and not slug and not title:
            raise ExcelValidationError(
                f"Row {index + 2} must include an identifier column: ID, link, slug or title"
            )

        primary_values = _parse_keywords(row.get(column_map.get("primary_keyword")))
        primary_keyword = primary_values[0] if primary_values else None
        secondary_keywords = _dedupe(
            [
                *primary_values[1:],
                *_parse_keywords(row.get(column_map.get("secondary_keywords"))),
            ]
        )
        focus_keywords = _dedupe(
            [*([primary_keyword] if primary_keyword else []), *secondary_keywords]
        )

        updates.append(
            PostUpdate(
                row_number=index + 2,
                post_id=post_id,
                link=link,
                title=title,
                content=_clean(row.get(column_map.get("content"))),
                featured_image_url=_clean(row.get(column_map.get("featured_image_url"))),
                category=_clean(row.get(column_map.get("category"))),
                tags=_parse_tags(row.get(column_map.get("tags"))),
                status=_clean(row.get(column_map.get("status"))),
                publish_date=_clean(row.get(column_map.get("publish_date"))),
                slug=slug,
                seo_title=_clean(row.get(column_map.get("seo_title"))),
                meta_description=_clean(row.get(column_map.get("meta_description"))),
                focus_keywords=focus_keywords,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords,
            )
        )

    return updates


def _parse_post_id(value: Any) -> int | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _read_best_sheet(pd, path: Path, sheet_name: str | int | None):
    try:
        with pd.ExcelFile(path) as excel_file:
            candidate_sheets: list[str | int]
            if sheet_name is not None:
                candidate_sheets = [sheet_name]
            else:
                named_sheets = list(excel_file.sheet_names)
                preferred = [
                    sheet for sheet in named_sheets if "bai seo html" in _normalize_label(sheet)
                ]
                candidate_sheets = [*preferred, *[sheet for sheet in named_sheets if sheet not in preferred]]

            last_error: Exception | None = None
            for candidate in candidate_sheets:
                try:
                    frame = excel_file.parse(sheet_name=candidate)
                except Exception as exc:
                    last_error = exc
                    continue
                column_map = _build_column_map(frame.columns)
                if REQUIRED_COLUMNS <= set(column_map):
                    return frame, column_map
    except Exception as exc:
        if isinstance(exc, ExcelValidationError):
            raise
        raise ExcelValidationError(f"Cannot read Excel file: {exc}") from exc

    if last_error and sheet_name is not None:
        raise ExcelValidationError(f"Cannot read Excel sheet {sheet_name!r}: {last_error}") from last_error
    raise ExcelValidationError(
        "No worksheet contains recognizable title/content columns. "
        "Supported examples: title/content or Tiêu đề SEO/Nội dung HTML thuần."
    )


def _read_update_sheet(pd, path: Path, sheet_name: str | int | None):
    last_error: Exception | None = None
    try:
        with pd.ExcelFile(path) as excel_file:
            candidate_sheets: list[str | int]
            if sheet_name is not None:
                candidate_sheets = [sheet_name]
            else:
                named_sheets = list(excel_file.sheet_names)
                preferred = [
                    sheet for sheet in named_sheets if "bai seo html" in _normalize_label(sheet)
                ]
                candidate_sheets = [*preferred, *[sheet for sheet in named_sheets if sheet not in preferred]]

            best: tuple[Any, dict[str, Any]] | None = None
            for candidate in candidate_sheets:
                try:
                    frame = excel_file.parse(sheet_name=candidate)
                except Exception as exc:
                    last_error = exc
                    continue
                column_map = _build_column_map(frame.columns)
                if not (UPDATE_IDENTIFIER_COLUMNS & set(column_map)):
                    continue
                # Prefer a sheet that also carries data columns beyond identifiers.
                if len(set(column_map) - UPDATE_IDENTIFIER_COLUMNS) > 0:
                    return frame, column_map
                if best is None:
                    best = (frame, column_map)
            if best is not None:
                return best
    except Exception as exc:
        if isinstance(exc, ExcelValidationError):
            raise
        raise ExcelValidationError(f"Cannot read Excel file: {exc}") from exc

    if last_error and sheet_name is not None:
        raise ExcelValidationError(f"Cannot read Excel sheet {sheet_name!r}: {last_error}") from last_error
    raise ExcelValidationError(
        "No worksheet contains an identifier column for updating posts. "
        "Supported examples: ID, Link bài viết, Slug or Tiêu đề SEO."
    )


def _build_column_map(columns) -> dict[str, Any]:
    normalized_to_original = {_normalize_label(column): column for column in columns}
    column_map: dict[str, Any] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            original = normalized_to_original.get(_normalize_label(alias))
            if original is not None:
                column_map[canonical] = original
                break
    return column_map


def _normalize_label(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.lower().replace("_", " ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _post_code_from_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    text = slug.strip()
    text = text.split("?", 1)[0].split("#", 1)[0]
    if "://" in text:
        text = text.rstrip("/").rsplit("/", 1)[-1]
    text = text.strip("/")
    return text or None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output

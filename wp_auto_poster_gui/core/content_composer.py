from __future__ import annotations

import html
import re

from .models import IMAGE_SIZE_WIDTH, UploadedMedia

# Match any block-level HTML element: <p>, <h2>, <h3>, <h4>, <ul>, <ol>, <table>, <blockquote>, <div>, <section>
_BLOCK_TAG_RE = re.compile(
    r"(<(?:p|h[1-6]|ul|ol|li|table|blockquote|div|section|figure|figcaption)\b[^>]*>.*?</(?:p|h[1-6]|ul|ol|li|table|blockquote|div|section|figure|figcaption)>)",
    re.IGNORECASE | re.DOTALL,
)

_P_TAG_RE = re.compile(r"(<p\b[^>]*>.*?</p>)", re.IGNORECASE | re.DOTALL)
_IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=["\'])([^"\']+)(["\'][^>]*>)', re.IGNORECASE)


def _image_html(
    media: UploadedMedia,
    title: str,
    alignment: str = "aligncenter",
    display_size: str = "auto",
    custom_width: int = 800,
) -> str:
    """Build an ``<img>`` tag wrapped in ``<p>`` with configurable alignment and size."""

    alt = html.escape(title, quote=True)
    src = html.escape(media.source_url, quote=True)
    css_class = f"wp-image-{media.media_id} {alignment}"

    # Build width / style attributes based on display_size
    attrs = ""
    if display_size == "full":
        attrs = ' style="width:100%;height:auto"'
    elif display_size == "custom":
        attrs = f' width="{custom_width}"'
    else:
        width = IMAGE_SIZE_WIDTH.get(display_size)
        if width is not None:
            attrs = f' width="{width}"'

    return (
        f'<p><img src="{src}" alt="{alt}" '
        f'class="{css_class}"{attrs} /></p>'
    )


def _split_paragraphs(content: str) -> tuple[list[str], str]:
    stripped = content.strip()
    if not stripped:
        return [], "plain"

    # Try block-level HTML elements first (broader than just <p>)
    html_parts = [part for part in _BLOCK_TAG_RE.split(content) if part]
    block_segments = [part for part in html_parts if _BLOCK_TAG_RE.fullmatch(part)]
    if block_segments:
        return html_parts, "html"

    # Fallback: plain text split by double newlines
    plain_segments = [segment.strip() for segment in re.split(r"\n\s*\n", content) if segment.strip()]
    return plain_segments, "plain"


def _replace_local_image_sources(content: str, uploaded_images: list[UploadedMedia]) -> tuple[str, set[int]]:
    filename_to_media = {
        media.filename.lower(): media
        for media in uploaded_images
        if media.filename
    }
    used_media_ids: set[int] = set()

    def replace(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        filename = src.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].split("?", 1)[0].lower()
        media = filename_to_media.get(filename)
        if not media:
            return match.group(0)
        used_media_ids.add(media.media_id)
        escaped_src = html.escape(media.source_url, quote=True)
        return f"{prefix}{escaped_src}{suffix}"

    return _IMG_SRC_RE.sub(replace, content), used_media_ids


def compose_content_with_images(
    content: str,
    title: str,
    uploaded_images: list[UploadedMedia],
    leading_images: list[UploadedMedia] | None = None,
    alignment: str = "aligncenter",
    display_size: str = "auto",
    custom_width: int = 800,
) -> str:
    """Insert uploaded content images evenly through the post body."""

    leading_images = leading_images or []
    all_uploaded_images = [*leading_images, *uploaded_images]
    if not all_uploaded_images:
        return content

    content, replaced_media_ids = _replace_local_image_sources(content, all_uploaded_images)
    leading_images = [media for media in leading_images if media.media_id not in replaced_media_ids]
    uploaded_images = [media for media in uploaded_images if media.media_id not in replaced_media_ids]
    if leading_images:
        leading_tags = [
            _image_html(media, title, alignment, display_size, custom_width)
            for media in leading_images
        ]
        prefix = "\n".join(leading_tags)
        content = f"{prefix}\n{content.lstrip()}" if content.strip() else prefix

    if not uploaded_images:
        return content

    segments, mode = _split_paragraphs(content)
    image_tags = [
        _image_html(media, title, alignment, display_size, custom_width)
        for media in uploaded_images
    ]

    if not segments:
        suffix = "\n".join(image_tags)
        return f"{content.rstrip()}\n{suffix}" if content.strip() else suffix

    paragraph_indexes: list[int]
    if mode == "html":
        # Insert after any block element, not just <p>
        paragraph_indexes = [i for i, part in enumerate(segments) if _BLOCK_TAG_RE.fullmatch(part)]
    else:
        paragraph_indexes = list(range(len(segments)))

    if not paragraph_indexes:
        return f"{content.rstrip()}\n" + "\n".join(image_tags)

    positions: dict[int, list[str]] = {}
    m = len(paragraph_indexes)
    n = len(image_tags)
    for k, tag in enumerate(image_tags, start=1):
        paragraph_position = round(k * (m + 1) / (n + 1))
        paragraph_position = max(1, min(m, paragraph_position))
        insert_after_index = paragraph_indexes[paragraph_position - 1]
        positions.setdefault(insert_after_index, []).append(tag)

    output: list[str] = []
    for i, segment in enumerate(segments):
        output.append(segment)
        output.extend(positions.get(i, []))

    separator = "" if mode == "html" else "\n\n"
    return separator.join(output)

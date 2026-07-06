from __future__ import annotations

import html
import re

from .models import IMAGE_SIZE_WIDTH, UploadedMedia

_P_TAG_RE = re.compile(r"(<p\b[^>]*>.*?</p>)", re.IGNORECASE | re.DOTALL)


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

    html_parts = [part for part in _P_TAG_RE.split(content) if part]
    p_segments = [part for part in html_parts if _P_TAG_RE.fullmatch(part)]
    if p_segments:
        return html_parts, "html"

    plain_segments = [segment.strip() for segment in re.split(r"\n\s*\n", content) if segment.strip()]
    return plain_segments, "plain"


def compose_content_with_images(
    content: str,
    title: str,
    uploaded_images: list[UploadedMedia],
    alignment: str = "aligncenter",
    display_size: str = "auto",
    custom_width: int = 800,
) -> str:
    """Insert uploaded content images evenly through the post body."""

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
        paragraph_indexes = [i for i, part in enumerate(segments) if _P_TAG_RE.fullmatch(part)]
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

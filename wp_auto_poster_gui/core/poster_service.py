from __future__ import annotations

from pathlib import Path
import time
from threading import Event
from typing import Callable, Iterable

from .content_composer import compose_content_with_images
from .excel_reader import read_posts_from_excel
from .image_matcher import match_images_for_posts
from .models import Post, PostResult, PosterOptions, ProgressCallback, UploadedMedia, WordPressConfig


ClientFactory = Callable[[WordPressConfig], object]


def _default_progress(message: str) -> None:
    del message


def _make_client(config: WordPressConfig):
    from .wp_client import WordPressClient

    return WordPressClient(config)


def publish_posts(
    posts: Iterable[Post],
    config: WordPressConfig,
    options: PosterOptions,
    image_folder: str | Path | None = None,
    progress_callback: ProgressCallback | None = None,
    stop_event: Event | None = None,
    client_factory: ClientFactory = _make_client,
) -> tuple[list[PostResult], list[Path]]:
    """Publish posts through WordPress. Tests can inject a fake client_factory."""

    progress = progress_callback or _default_progress
    post_list = list(posts)
    ma_bai_values = [post.ma_bai or "" for post in post_list if post.ma_bai]
    image_matches, orphan_files = match_images_for_posts(
        image_folder,
        ma_bai_values,
        max_images_per_post=options.max_images_per_post,
    )
    client = client_factory(config)
    results: list[PostResult] = []

    for post in post_list:
        if stop_event and stop_event.is_set():
            progress("Stopped by user")
            break

        progress(f"Processing row {post.row_number}: {post.title}")
        if options.default_status and not post.status:
            post.status = options.default_status

        try:
            if options.skip_duplicates:
                duplicate_post = _find_duplicate_post(client, post.title)
                if duplicate_post:
                    if options.dry_run:
                        results.append(PostResult(post.row_number, post.title, "success", link="dry-run-update"))
                        progress(f"Would update duplicate SEO fields: {post.title}")
                        continue
                    duplicate_id = duplicate_post.get("id")
                    if duplicate_id is not None and hasattr(client, "update_post_seo"):
                        payload = getattr(client, "update_post_seo")(int(duplicate_id), post)
                        link = _post_link(payload) or _post_link(duplicate_post)
                        results.append(
                            PostResult(
                                post.row_number,
                                post.title,
                                "success",
                                link=link,
                                error="Updated existing duplicate SEO fields",
                            )
                        )
                        progress(f"Updated duplicate SEO fields: {post.title}")
                        continue
                    results.append(PostResult(post.row_number, post.title, "skipped", error="Duplicate title"))
                    progress(f"Skipped duplicate: {post.title}")
                    continue

            matched = image_matches.get(post.ma_bai or "", None)
            featured_media_id: int | None = None
            if matched and matched.background:
                media = getattr(client, "upload_media_from_path")(matched.background)
                featured_media_id = media.media_id
            elif post.featured_image_url:
                media = getattr(client, "upload_media_from_url")(post.featured_image_url)
                featured_media_id = media.media_id

            uploaded_content: list[UploadedMedia] = []
            if matched:
                for image_path in matched.content_images:
                    uploaded_content.append(getattr(client, "upload_media_from_path")(image_path))

            content = compose_content_with_images(post.content, post.title, uploaded_content)
            if options.dry_run:
                results.append(PostResult(post.row_number, post.title, "success", link="dry-run"))
                continue

            payload = getattr(client, "create_post")(post, content, featured_media_id)
            link = payload.get("link") if isinstance(payload, dict) else None
            results.append(PostResult(post.row_number, post.title, "success", link=link))
            progress(f"Posted: {post.title}")

            if config.delay_seconds > 0:
                time.sleep(config.delay_seconds)
        except Exception as exc:
            results.append(PostResult(post.row_number, post.title, "failed", error=str(exc)))
            progress(f"Failed row {post.row_number}: {exc}")

    return results, orphan_files


def _find_duplicate_post(client: object, title: str) -> dict | None:
    if hasattr(client, "find_post_by_title"):
        return getattr(client, "find_post_by_title")(title)
    if getattr(client, "check_duplicate_by_title")(title):
        return {"id": None}
    return None


def _post_link(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    link = payload.get("link")
    if isinstance(link, str):
        return link
    return None


def publish_from_excel(
    excel_path: str | Path,
    image_folder: str | Path | None,
    config: WordPressConfig,
    options: PosterOptions,
    progress_callback: ProgressCallback | None = None,
    stop_event: Event | None = None,
    client_factory: ClientFactory = _make_client,
) -> tuple[list[PostResult], list[Path]]:
    posts = read_posts_from_excel(excel_path, default_status=options.default_status)
    return publish_posts(
        posts,
        config,
        options,
        image_folder=image_folder,
        progress_callback=progress_callback,
        stop_event=stop_event,
        client_factory=client_factory,
    )


def export_results_to_excel(results: list[PostResult], output_path: str | Path) -> None:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("pandas and openpyxl are required to export Excel reports") from exc

    frame = pd.DataFrame(
        [
            {
                "row": result.row_number,
                "title": result.title,
                "status": result.status,
                "link": result.link,
                "error": result.error,
            }
            for result in results
        ]
    )
    frame.to_excel(output_path, index=False)

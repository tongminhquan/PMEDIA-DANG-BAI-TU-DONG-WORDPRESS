from __future__ import annotations

import tempfile
from pathlib import Path
import time
from threading import Event
from typing import Callable, Iterable
from zipfile import ZipFile

from .content_composer import compose_content_with_images
from .excel_reader import read_posts_from_excel
from .image_matcher import SUPPORTED_IMAGE_EXTENSIONS, match_images_for_posts
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
            duplicate_post = _find_duplicate_post(client, post.title) if options.skip_duplicates else None

            matched = image_matches.get(post.ma_bai or "", None)
            featured_media_id: int | None = None
            if matched and matched.background:
                media = getattr(client, "upload_media_from_path")(matched.background)
                featured_media_id = media.media_id
                progress(f"Uploaded featured image: {matched.background.name} -> {media.source_url}")
            elif post.featured_image_url:
                media = getattr(client, "upload_media_from_url")(post.featured_image_url)
                featured_media_id = media.media_id
                progress(f"Uploaded featured image URL: {media.source_url}")

            uploaded_content: list[UploadedMedia] = []
            if matched:
                for image_path in matched.content_images:
                    media = getattr(client, "upload_media_from_path")(image_path)
                    uploaded_content.append(media)
                    progress(f"Uploaded content image: {image_path.name} -> {media.source_url}")

            content = compose_content_with_images(
                post.content,
                post.title,
                uploaded_content,
                alignment=options.image_alignment,
                display_size=options.image_display_size,
                custom_width=options.image_custom_width,
            )

            if options.skip_duplicates:
                if duplicate_post:
                    if options.dry_run:
                        results.append(PostResult(post.row_number, post.title, "success", link="dry-run-update"))
                        progress(f"Would update duplicate post: {post.title}")
                        continue
                    duplicate_id = duplicate_post.get("id")
                    if duplicate_id is not None and hasattr(client, "update_post"):
                        payload = getattr(client, "update_post")(int(duplicate_id), post, content, featured_media_id)
                        link = _post_link(payload) or _post_link(duplicate_post)
                        results.append(
                            PostResult(
                                post.row_number,
                                post.title,
                                "success",
                                link=link,
                                error="Updated existing duplicate post content and SEO fields",
                            )
                        )
                        progress(f"Updated duplicate post content, images and SEO fields: {post.title}")
                        continue
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
    progress = progress_callback or _default_progress
    prepared_source, cleanup = _prepare_image_source(excel_path, image_folder, posts, options, progress)
    try:
        return publish_posts(
            posts,
            config,
            options,
            image_folder=prepared_source,
            progress_callback=progress_callback,
            stop_event=stop_event,
            client_factory=client_factory,
        )
    finally:
        if cleanup is not None:
            cleanup.cleanup()


def _prepare_image_source(
    excel_path: str | Path,
    image_source: str | Path | None,
    posts: list[Post],
    options: PosterOptions,
    progress: ProgressCallback,
) -> tuple[Path | None, tempfile.TemporaryDirectory | None]:
    ma_bai_values = [post.ma_bai or "" for post in posts if post.ma_bai]
    if not ma_bai_values:
        return Path(image_source) if image_source else None, None

    selected = Path(image_source) if image_source else None
    if selected:
        if selected.suffix.lower() == ".zip" and selected.exists():
            temp_dir = tempfile.TemporaryDirectory(prefix="wp-auto-poster-images-")
            extracted = _extract_matching_images_from_zip(selected, ma_bai_values, Path(temp_dir.name))
            progress(f"Đã đọc file ZIP ảnh: {selected.name} ({extracted} ảnh khớp)")
            return Path(temp_dir.name), temp_dir
        try:
            matches, _orphans = match_images_for_posts(selected, ma_bai_values, options.max_images_per_post)
            if _matched_image_count(matches) > 0:
                return selected, None
            progress(f"Thư mục ảnh đang chọn không khớp mã bài: {selected}")
        except FileNotFoundError:
            progress(f"Không tìm thấy thư mục/file ảnh: {selected}")

    detected = _find_matching_image_source(Path(excel_path).parent, ma_bai_values)
    if not detected:
        return selected, None

    if detected.suffix.lower() == ".zip":
        temp_dir = tempfile.TemporaryDirectory(prefix="wp-auto-poster-images-")
        extracted = _extract_matching_images_from_zip(detected, ma_bai_values, Path(temp_dir.name))
        progress(f"Tự nhận file ZIP ảnh: {detected.name} ({extracted} ảnh khớp)")
        return Path(temp_dir.name), temp_dir

    progress(f"Tự nhận thư mục ảnh: {detected}")
    return detected, None


def _find_matching_image_source(base_dir: Path, ma_bai_values: list[str]) -> Path | None:
    if not base_dir.exists():
        return None
    candidates = [
        item
        for item in base_dir.iterdir()
        if item.is_dir() or item.suffix.lower() == ".zip"
    ]
    candidates = [
        item
        for item in candidates
        if any(token in item.name.lower() for token in ["anh", "hinh", "image", "photo", "seo"])
    ]
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    for candidate in candidates:
        try:
            if candidate.suffix.lower() == ".zip":
                if _zip_match_count(candidate, ma_bai_values) > 0:
                    return candidate
            else:
                matches, _orphans = match_images_for_posts(candidate, ma_bai_values)
                if _matched_image_count(matches) > 0:
                    return candidate
        except Exception:
            continue
    return None


def _zip_match_count(zip_path: Path, ma_bai_values: list[str]) -> int:
    count = 0
    prefixes = tuple(f"{code}_".lower() for code in ma_bai_values if code)
    with ZipFile(zip_path) as archive:
        for entry in archive.infolist():
            name = Path(entry.filename).name
            suffix = Path(name).suffix.lower()
            if not name or suffix not in SUPPORTED_IMAGE_EXTENSIONS:
                continue
            if name.lower().startswith(prefixes):
                count += 1
    return count


def _extract_matching_images_from_zip(zip_path: Path, ma_bai_values: list[str], output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefixes = tuple(f"{code}_".lower() for code in ma_bai_values if code)
    count = 0
    with ZipFile(zip_path) as archive:
        for entry in archive.infolist():
            name = Path(entry.filename).name
            suffix = Path(name).suffix.lower()
            if not name or suffix not in SUPPORTED_IMAGE_EXTENSIONS:
                continue
            if not name.lower().startswith(prefixes):
                continue
            target = output_dir / name
            with archive.open(entry) as source, target.open("wb") as destination:
                destination.write(source.read())
            count += 1
    return count


def _matched_image_count(matches: dict) -> int:
    total = 0
    for match in matches.values():
        if match.background:
            total += 1
        total += len(match.content_images)
    return total


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

from __future__ import annotations

from pathlib import Path
import re

from .models import MatchedImages

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
FEATURED_IMAGE_SUFFIXES = {"bg", "thumb", "thumbnail", "featured"}


def match_images_for_posts(
    image_folder: str | Path | None,
    ma_bai_values: list[str],
    max_images_per_post: int = 2,
) -> tuple[dict[str, MatchedImages], list[Path]]:
    """Match local image files to post codes using `{ma_bai}_bg`/`_thumb` and `{ma_bai}_1` names."""

    matches = {code: MatchedImages() for code in ma_bai_values if code}
    if not image_folder:
        return matches, []

    folder = Path(image_folder)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Image folder does not exist: {folder}")

    known_codes = sorted(matches.keys(), key=len, reverse=True)
    numbered: dict[str, list[tuple[int, Path]]] = {code: [] for code in known_codes}
    orphan_files: list[Path] = []

    for file_path in sorted(folder.iterdir(), key=lambda path: path.name.lower()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue

        stem = file_path.stem
        matched = False
        for code in known_codes:
            prefix = f"{code}_"
            if not stem.lower().startswith(prefix.lower()):
                continue
            suffix = stem[len(prefix) :]
            if suffix.lower() in FEATURED_IMAGE_SUFFIXES:
                matches[code].background = file_path
                matched = True
                break
            numeric = re.fullmatch(r"(\d+)", suffix)
            if numeric:
                numbered[code].append((int(numeric.group(1)), file_path))
                matched = True
                break
        if not matched:
            orphan_files.append(file_path)

    for code, items in numbered.items():
        ordered = [path for _, path in sorted(items, key=lambda item: (item[0], item[1].name.lower()))]
        matches[code].content_images = ordered[: max(0, max_images_per_post)]

    return matches, orphan_files

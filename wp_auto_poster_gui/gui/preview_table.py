from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from wp_auto_poster_gui.core.models import MatchedImages, Post, PostResult


def fill_preview_table(
    table: QTableWidget,
    posts: list[Post],
    image_matches: dict[str, MatchedImages],
) -> None:
    headers = [
        "#",
        "Mã bài",
        "Tiêu đề",
        "Chuyên mục",
        "Tags",
        "Trạng thái",
        "Ngày đăng",
        "Ảnh nền",
        "Số ảnh nội dung",
    ]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(posts))
    for row_index, post in enumerate(posts):
        match = image_matches.get(post.ma_bai or "", MatchedImages())
        featured_status = "✅ local" if match.background else ("🌐 URL" if post.featured_image_url else "❌")
        values = [
            str(post.row_number),
            post.ma_bai or "",
            post.title,
            post.category or "",
            ", ".join(post.tags),
            post.status,
            post.publish_date or "",
            featured_status,
            str(len(match.content_images)),
        ]
        for column, value in enumerate(values):
            table.setItem(row_index, column, QTableWidgetItem(value))
    table.resizeColumnsToContents()


def fill_result_table(table: QTableWidget, results: list[PostResult]) -> None:
    headers = ["#", "Tiêu đề", "Kết quả", "Link", "Ghi chú / lỗi"]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(results))
    for row_index, result in enumerate(results):
        values = [
            str(result.row_number),
            result.title,
            result.status,
            result.link or "",
            result.error or "",
        ]
        for column, value in enumerate(values):
            table.setItem(row_index, column, QTableWidgetItem(value))
    table.resizeColumnsToContents()


def orphan_label_text(orphan_files: list[Path]) -> str:
    if not orphan_files:
        return ""
    names = ", ".join(path.name for path in orphan_files[:20])
    suffix = "" if len(orphan_files) <= 20 else f" và {len(orphan_files) - 20} file khác"
    return f"⚠ Ảnh không khớp mã bài nào: {names}{suffix}"

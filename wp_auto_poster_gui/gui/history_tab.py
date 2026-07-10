from __future__ import annotations

from collections import Counter
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from wp_auto_poster_gui.core.history_store import RunHistoryRecord, RunHistoryStore
from wp_auto_poster_gui.core.website_post_store import WebsitePostSnapshot, WebsitePostStore


class HistoryTab(QWidget):
    website_refresh_requested = Signal()

    def __init__(self, store: RunHistoryStore, website_store: WebsitePostStore | None = None):
        super().__init__()
        self.store = store
        self.website_store = website_store
        self.records: list[RunHistoryRecord] = []
        self.current_snapshot: WebsitePostSnapshot | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        self.views = QTabWidget()
        self.views.addTab(self._build_run_history_page(), "Lần chạy của app")
        self.views.addTab(self._build_website_history_page(), "Toàn bộ bài trên website")
        layout.addWidget(self.views)

        self.refresh()
        self.set_website_snapshot(None)

    def _build_run_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        title = QLabel("Lịch sử các lần chạy")
        title.setObjectName("sectionTitle")
        refresh_button = QPushButton("Làm mới")
        refresh_button.clicked.connect(self.refresh)
        top_row.addWidget(title)
        top_row.addStretch(1)
        top_row.addWidget(refresh_button)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._show_selected_detail)

        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        self.detail_box.setMinimumHeight(170)

        layout.addLayout(top_row)
        layout.addWidget(self.table, 3)
        layout.addWidget(QLabel("Chi tiết"))
        layout.addWidget(self.detail_box, 2)
        return page

    def _build_website_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self.website_summary_label = QLabel("Chưa đồng bộ bài viết từ website.")
        self.website_summary_label.setObjectName("mutedLabel")
        sync_button = QPushButton("Đồng bộ toàn bộ bài")
        sync_button.clicked.connect(self.website_refresh_requested.emit)
        top_row.addWidget(self.website_summary_label, 1)
        top_row.addWidget(sync_button)

        self.website_table = QTableWidget()
        self.website_table.setAlternatingRowColors(True)
        self.website_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.website_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addLayout(top_row)
        layout.addWidget(self.website_table, 1)
        return page

    def refresh(self) -> None:
        self.records = self.store.load_records()
        headers = [
            "Thời gian",
            "Kiểu",
            "File Excel",
            "Tổng",
            "Thành công",
            "Lỗi",
            "Bỏ qua",
            "File kết quả",
            "Ghi chú",
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(self.records))

        for row_index, record in enumerate(self.records):
            values = [
                record.finished_at,
                _mode_label(record.mode),
                _name_or_blank(record.excel_path),
                str(record.total),
                str(record.success),
                str(record.failed),
                str(record.skipped),
                _name_or_blank(record.export_excel_path),
                record.summary or record.error or "",
            ]
            tooltips = [
                record.run_id,
                record.mode,
                record.excel_path,
                "",
                "",
                "",
                "",
                record.export_excel_path or "",
                record.error or record.summary,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if tooltips[column]:
                    item.setToolTip(tooltips[column])
                self.table.setItem(row_index, column, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        if self.records:
            self.table.selectRow(0)
        else:
            self.detail_box.setPlainText("Chưa có lịch sử chạy.")

    def show_cached_website(self, site_url: str) -> None:
        snapshot = self.website_store.get_snapshot(site_url) if self.website_store and site_url else None
        self.set_website_snapshot(snapshot, site_url)

    def set_website_loading(self, loading: bool, site_url: str = "") -> None:
        if loading:
            suffix = f" từ {site_url.rstrip('/')}" if site_url else ""
            self.website_summary_label.setText(f"Đang đồng bộ toàn bộ bài viết{suffix}...")

    def set_website_snapshot(
        self,
        snapshot: WebsitePostSnapshot | None,
        site_url: str = "",
    ) -> None:
        self.current_snapshot = snapshot
        posts = snapshot.posts if snapshot else []
        headers = ["ID", "Trạng thái", "Ngày đăng", "Cập nhật", "Tiêu đề", "Slug", "Link"]
        self.website_table.setColumnCount(len(headers))
        self.website_table.setHorizontalHeaderLabels(headers)
        self.website_table.setRowCount(len(posts))

        for row_index, post in enumerate(posts):
            values = [
                str(post.post_id),
                post.status,
                post.date,
                post.modified,
                post.title,
                post.slug,
                post.link,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 6 and value:
                    item.setToolTip(value)
                self.website_table.setItem(row_index, column, item)

        self.website_table.resizeColumnsToContents()
        self.website_table.horizontalHeader().setStretchLastSection(True)
        if snapshot:
            counts = Counter(post.status or "không rõ" for post in posts)
            status_text = ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))
            suffix = f" | {status_text}" if status_text else ""
            self.website_summary_label.setText(
                f"{snapshot.site_url} | {snapshot.total} bài | Đồng bộ: {snapshot.synced_at}{suffix}"
            )
        else:
            label = site_url.rstrip("/") if site_url else "website đang chọn"
            self.website_summary_label.setText(
                f"Chưa có dữ liệu bài viết của {label}. Bấm Đồng bộ toàn bộ bài."
            )

    def _show_selected_detail(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.records):
            return
        record = self.records[row]
        lines = [
            f"ID: {record.run_id}",
            f"Thời gian bắt đầu: {record.started_at}",
            f"Thời gian hoàn tất: {record.finished_at}",
            f"Kiểu chạy: {_mode_label(record.mode)}",
            f"File Excel: {record.excel_path}",
            f"Thư mục ảnh: {record.image_folder or ''}",
            f"File Excel kết quả: {record.export_excel_path or ''}",
            f"Kết quả: {record.success}/{record.total} thành công, {record.failed} lỗi, {record.skipped} bỏ qua",
        ]
        if record.summary:
            lines.append(f"Ghi chú: {record.summary}")
        if record.error:
            lines.append(f"Lỗi chung: {record.error}")
        if record.orphan_files:
            lines.append("Ảnh không khớp: " + ", ".join(record.orphan_files[:20]))
            if len(record.orphan_files) > 20:
                lines.append(f"... và {len(record.orphan_files) - 20} file khác")

        lines.append("")
        lines.append("Chi tiết từng bài:")
        if not record.results:
            lines.append("- Không có kết quả từng bài.")
        for item in record.results[:250]:
            note = item.link or item.error or ""
            lines.append(f"- Dòng {item.row_number}: [{item.status}] {item.title} {note}")
        if len(record.results) > 250:
            lines.append(f"... và {len(record.results) - 250} dòng khác")

        self.detail_box.setPlainText("\n".join(lines))


def _mode_label(mode: str) -> str:
    labels = {
        "scheduled": "Lịch tự động",
        "manual": "Thủ công",
        "website_bulk_publish": "Xuất bản bài trên web",
        "website_image_layout": "Sửa ảnh bài trên web",
        "website_excel_update": "Cập nhật bài từ Excel",
    }
    return labels.get(mode, mode)


def _name_or_blank(value: str | None) -> str:
    return Path(value).name if value else ""

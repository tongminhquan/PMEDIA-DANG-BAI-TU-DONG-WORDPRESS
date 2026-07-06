from __future__ import annotations

from pathlib import Path
import json
from threading import Event

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Mapping from display label to internal value
_IMAGE_SIZE_OPTIONS = [
    ("Tự động", "auto"),
    ("Nhỏ (300px)", "small"),
    ("Vừa (600px)", "medium"),
    ("Lớn (900px)", "large"),
    ("Toàn chiều rộng", "full"),
    ("Tùy chỉnh", "custom"),
]

_IMAGE_ALIGN_OPTIONS = [
    ("Giữa", "aligncenter"),
    ("Trái", "alignleft"),
    ("Phải", "alignright"),
    ("Không căn", "alignnone"),
]

from wp_auto_poster_gui.core.excel_reader import ExcelValidationError, read_posts_from_excel
from wp_auto_poster_gui.core.image_matcher import match_images_for_posts
from wp_auto_poster_gui.core.models import PosterOptions, WordPressConfig
from wp_auto_poster_gui.core.poster_service import export_results_to_excel, publish_from_excel
from wp_auto_poster_gui.core.scheduler_service import SchedulerService
from wp_auto_poster_gui.app_info import APP_ICON_PATH, APP_NAME
from wp_auto_poster_gui.gui.config_dialog import AdvancedSettingsDialog
from wp_auto_poster_gui.gui.preview_table import fill_preview_table, fill_result_table, orphan_label_text
from wp_auto_poster_gui.gui.schedule_tab import ScheduleTab
from wp_auto_poster_gui.gui.tray_icon import create_tray_icon
from wp_auto_poster_gui.gui.workers import ConnectionTestWorker, PosterWorker


class MainWindow(QMainWindow):
    schedule_message = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1180, 760)

        self.settings_path = Path("config/settings.json")
        self.scheduler = SchedulerService("config/schedule.json")
        self.results = []
        self.poster_worker: PosterWorker | None = None
        self.connection_worker: ConnectionTestWorker | None = None
        self.stop_event = Event()
        self._quitting = False

        self.delay_seconds = 0
        self.retry_count = 3
        self.timeout_seconds = 30

        self._build_ui()
        self._load_settings()

        self.tray_icon = create_tray_icon(self, self.windowIcon() or QIcon())
        self.schedule_message.connect(lambda message: self.tray_icon.showMessage(APP_NAME, message))
        self.schedule_tab.load_config(self.scheduler.config)
        self._apply_schedule()

    def _build_ui(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._manual_tab(), "Đăng thủ công")
        self.schedule_tab = ScheduleTab()
        self.schedule_tab.config_changed.connect(self._on_schedule_changed)
        tabs.addTab(self.schedule_tab, "Lịch tự động")
        self.setCentralWidget(tabs)

    def _manual_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        connection_box = QGroupBox("Kết nối WordPress")
        connection_form = QFormLayout(connection_box)
        self.site_url_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.connection_status = QLabel("Chưa kiểm tra")
        save_button = QPushButton("Lưu")
        save_button.clicked.connect(self._save_settings)
        test_button = QPushButton("Kiểm tra kết nối")
        test_button.clicked.connect(self._test_connection)
        advanced_button = QPushButton("Cài đặt nâng cao")
        advanced_button.clicked.connect(self._open_advanced_settings)

        actions = QHBoxLayout()
        actions.addWidget(save_button)
        actions.addWidget(test_button)
        actions.addWidget(advanced_button)
        actions.addStretch(1)

        connection_form.addRow("URL", self.site_url_edit)
        connection_form.addRow("Username", self.username_edit)
        connection_form.addRow("Application password", self.password_edit)
        connection_form.addRow("Trạng thái", self.connection_status)
        connection_form.addRow("", actions)

        source_box = QGroupBox("Nguồn dữ liệu")
        source_form = QFormLayout(source_box)
        self.excel_edit = QLineEdit()
        self.image_folder_edit = QLineEdit()
        self.max_images_spin = QSpinBox()
        self.max_images_spin.setRange(0, 50)
        self.max_images_spin.setValue(5)

        # Image display settings
        self.image_size_combo = QComboBox()
        for label, _value in _IMAGE_SIZE_OPTIONS:
            self.image_size_combo.addItem(label)
        self.image_custom_width_spin = QSpinBox()
        self.image_custom_width_spin.setRange(100, 2000)
        self.image_custom_width_spin.setValue(800)
        self.image_custom_width_spin.setSuffix(" px")
        self.image_custom_width_spin.setVisible(False)
        self.image_size_combo.currentIndexChanged.connect(self._on_image_size_changed)

        self.image_align_combo = QComboBox()
        for label, _value in _IMAGE_ALIGN_OPTIONS:
            self.image_align_combo.addItem(label)

        excel_button = QPushButton("Chọn Excel")
        excel_button.clicked.connect(self._choose_excel)
        image_button = QPushButton("Chọn thư mục ảnh")
        image_button.clicked.connect(self._choose_image_folder)

        excel_row = QHBoxLayout()
        excel_row.addWidget(self.excel_edit)
        excel_row.addWidget(excel_button)
        image_row = QHBoxLayout()
        image_row.addWidget(self.image_folder_edit)
        image_row.addWidget(image_button)

        image_size_row = QHBoxLayout()
        image_size_row.addWidget(self.image_size_combo)
        image_size_row.addWidget(self.image_custom_width_spin)
        image_size_row.addStretch(1)

        preview_button = QPushButton("Preview")
        preview_button.clicked.connect(self._refresh_preview)
        self.post_button = QPushButton("Đăng ngay")
        self.post_button.clicked.connect(self._start_publish)
        self.stop_button = QPushButton("Dừng")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._stop_publish)
        report_button = QPushButton("Xuất báo cáo Excel")
        report_button.clicked.connect(self._export_report)

        run_row = QHBoxLayout()
        run_row.addWidget(preview_button)
        run_row.addWidget(self.post_button)
        run_row.addWidget(self.stop_button)
        run_row.addWidget(report_button)
        run_row.addStretch(1)

        source_form.addRow("File Excel", excel_row)
        source_form.addRow("Thư mục ảnh", image_row)
        source_form.addRow("Ảnh tối đa mỗi bài", self.max_images_spin)
        source_form.addRow("Kích thước ảnh", image_size_row)
        source_form.addRow("Căn chỉnh ảnh", self.image_align_combo)
        source_form.addRow("", run_row)

        self.preview_table = QTableWidget()
        self.result_table = QTableWidget()
        self.orphan_label = QLabel()
        self.orphan_label.setWordWrap(True)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()

        tables = QSplitter(Qt.Vertical)
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.addWidget(QLabel("Preview"))
        preview_layout.addWidget(self.preview_table)
        preview_layout.addWidget(self.orphan_label)
        result_container = QWidget()
        result_layout = QVBoxLayout(result_container)
        result_layout.addWidget(QLabel("Kết quả"))
        result_layout.addWidget(self.result_table)
        tables.addWidget(preview_container)
        tables.addWidget(result_container)

        layout.addWidget(connection_box)
        layout.addWidget(source_box)
        layout.addWidget(tables, 1)
        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log_box)
        layout.addWidget(self.progress)
        return page

    def _choose_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel (*.xlsx *.xls)")
        if path:
            self.excel_edit.setText(path)
            self._refresh_preview()

    def _choose_image_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục ảnh")
        if path:
            self.image_folder_edit.setText(path)
            self._refresh_preview()

    def _refresh_preview(self) -> bool:
        excel_path = self.excel_edit.text().strip()
        if not excel_path:
            return False
        try:
            posts = read_posts_from_excel(excel_path)
            matches, orphan_files = match_images_for_posts(
                self.image_folder_edit.text().strip() or None,
                [post.ma_bai or "" for post in posts if post.ma_bai],
                self.max_images_spin.value(),
            )
            fill_preview_table(self.preview_table, posts, matches)
            self.orphan_label.setText(orphan_label_text(orphan_files))
            self._log(f"Preview {len(posts)} bài")
            return True
        except (ExcelValidationError, FileNotFoundError, RuntimeError, ValueError) as exc:
            QMessageBox.warning(self, "Không đọc được dữ liệu", str(exc))
            self._log(f"Lỗi preview: {exc}")
            return False

    def _current_config(self, show_errors: bool = True) -> WordPressConfig | None:
        site_url = self.site_url_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if not site_url or not username or not password:
            if show_errors:
                QMessageBox.warning(self, "Thiếu cấu hình", "Cần nhập URL, username và application password.")
            return None
        return WordPressConfig(
            site_url=site_url,
            username=username,
            application_password=password,
            timeout_seconds=self.timeout_seconds,
            retry_count=self.retry_count,
            delay_seconds=self.delay_seconds,
        )

    def _on_image_size_changed(self) -> None:
        """Show/hide custom width spin based on selected image size."""
        index = self.image_size_combo.currentIndex()
        size_value = _IMAGE_SIZE_OPTIONS[index][1] if index < len(_IMAGE_SIZE_OPTIONS) else "auto"
        self.image_custom_width_spin.setVisible(size_value == "custom")

    def _current_image_settings(self) -> tuple[str, str, int]:
        """Return (image_alignment, image_display_size, image_custom_width) from UI."""
        size_index = self.image_size_combo.currentIndex()
        display_size = _IMAGE_SIZE_OPTIONS[size_index][1] if size_index < len(_IMAGE_SIZE_OPTIONS) else "auto"
        align_index = self.image_align_combo.currentIndex()
        alignment = _IMAGE_ALIGN_OPTIONS[align_index][1] if align_index < len(_IMAGE_ALIGN_OPTIONS) else "aligncenter"
        custom_width = self.image_custom_width_spin.value()
        return alignment, display_size, custom_width

    def _poster_options(self, max_images: int | None = None, schedule_config=None) -> PosterOptions:
        if schedule_config is not None:
            return PosterOptions(
                max_images_per_post=max_images if max_images is not None else self.max_images_spin.value(),
                image_alignment=schedule_config.image_alignment,
                image_display_size=schedule_config.image_display_size,
                image_custom_width=schedule_config.image_custom_width,
            )
        alignment, display_size, custom_width = self._current_image_settings()
        return PosterOptions(
            max_images_per_post=max_images if max_images is not None else self.max_images_spin.value(),
            image_alignment=alignment,
            image_display_size=display_size,
            image_custom_width=custom_width,
        )

    def _test_connection(self) -> None:
        config = self._current_config()
        if not config:
            return
        self.connection_status.setText("Đang kiểm tra...")
        self.connection_worker = ConnectionTestWorker(config)
        self.connection_worker.finished_with_result.connect(self._on_connection_tested)
        self.connection_worker.start()

    def _on_connection_tested(self, ok: bool, message: str) -> None:
        self.connection_status.setText(("OK: " if ok else "Lỗi: ") + message)

    def _start_publish(self) -> None:
        if not self._refresh_preview():
            return
        config = self._current_config()
        if not config:
            return
        if QMessageBox.question(
            self,
            "Xác nhận đăng bài",
            "Ứng dụng sẽ gửi nội dung trong Excel lên WordPress theo trạng thái của từng dòng.",
        ) != QMessageBox.Yes:
            return

        self.stop_event.clear()
        self.progress.show()
        self.post_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.poster_worker = PosterWorker(
            self.excel_edit.text().strip(),
            self.image_folder_edit.text().strip() or None,
            config,
            self._poster_options(),
            self.stop_event,
        )
        self.poster_worker.progress.connect(self._log)
        self.poster_worker.completed.connect(self._on_publish_completed)
        self.poster_worker.start()

    def _stop_publish(self) -> None:
        self.stop_event.set()
        self._log("Đã yêu cầu dừng sau bài hiện tại")

    def _on_publish_completed(self, results, orphan_files) -> None:
        self.results = list(results)
        fill_result_table(self.result_table, self.results)
        self.orphan_label.setText(orphan_label_text(list(orphan_files)))
        self.progress.hide()
        self.post_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        success = sum(1 for result in self.results if result.status == "success")
        self._log(f"Hoàn tất: {success}/{len(self.results)} thành công")

    def _export_report(self) -> None:
        if not self.results:
            QMessageBox.information(self, "Chưa có kết quả", "Chưa có kết quả để xuất.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Xuất báo cáo", "wordpress_post_report.xlsx", "Excel (*.xlsx)")
        if path:
            export_results_to_excel(self.results, path)
            self._log(f"Đã xuất báo cáo: {path}")

    def _on_schedule_changed(self) -> None:
        self.scheduler.config = self.schedule_tab.to_config()
        self.scheduler.save_config()
        self._apply_schedule()

    def _apply_schedule(self) -> None:
        try:
            self.scheduler.start(self._run_scheduled_job)
            self.schedule_tab.set_next_run(self.scheduler.next_run_time())
        except Exception as exc:
            self.schedule_tab.set_next_run(f"Lỗi lịch: {exc}")
            self._log(f"Lỗi lịch: {exc}")

    def _run_scheduled_job(self) -> str:
        config = self._current_config(show_errors=False)
        if not config:
            raise RuntimeError("Thiếu cấu hình WordPress trong phiên hiện tại")
        schedule = self.scheduler.config
        results, _ = publish_from_excel(
            schedule.excel_path,
            schedule.image_folder or None,
            config,
            self._poster_options(schedule.max_images_per_post, schedule_config=schedule),
        )
        success = sum(1 for result in results if result.status == "success")
        summary = f"Đăng thành công {success}/{len(results)} bài"
        self.schedule_message.emit(summary)
        return summary

    def _open_advanced_settings(self) -> None:
        dialog = AdvancedSettingsDialog(self.delay_seconds, self.retry_count, self.timeout_seconds)
        if dialog.exec():
            self.delay_seconds, self.retry_count, self.timeout_seconds = dialog.values()
            self._save_settings()

    def _load_settings(self) -> None:
        if not self.settings_path.exists():
            return
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except Exception:
            return
        self.site_url_edit.setText(data.get("site_url", ""))
        self.username_edit.setText(data.get("username", ""))
        self.delay_seconds = int(data.get("delay_seconds", 0))
        self.retry_count = int(data.get("retry_count", 3))
        self.timeout_seconds = int(data.get("timeout_seconds", 30))

        # Restore image display settings
        saved_size = data.get("image_display_size", "auto")
        for i, (_label, value) in enumerate(_IMAGE_SIZE_OPTIONS):
            if value == saved_size:
                self.image_size_combo.setCurrentIndex(i)
                break
        saved_align = data.get("image_alignment", "aligncenter")
        for i, (_label, value) in enumerate(_IMAGE_ALIGN_OPTIONS):
            if value == saved_align:
                self.image_align_combo.setCurrentIndex(i)
                break
        self.image_custom_width_spin.setValue(int(data.get("image_custom_width", 800)))
        self._on_image_size_changed()

    def _save_settings(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        alignment, display_size, custom_width = self._current_image_settings()
        data = {
            "site_url": self.site_url_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "delay_seconds": self.delay_seconds,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "image_alignment": alignment,
            "image_display_size": display_size,
            "image_custom_width": custom_width,
        }
        self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._log("Đã lưu cấu hình không gồm password")

    def _log(self, message: str) -> None:
        self.log_box.append(message)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def show_normal_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_application(self) -> None:
        self._quitting = True
        self.scheduler.stop()
        QApplication.instance().quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._quitting:
            event.accept()
            return
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(APP_NAME, "Ứng dụng vẫn chạy ở khay hệ thống")

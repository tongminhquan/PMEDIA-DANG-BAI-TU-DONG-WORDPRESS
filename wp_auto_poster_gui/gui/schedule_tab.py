from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt, QTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QDateTimeEdit,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from wp_auto_poster_gui.core.scheduler_service import ScheduleConfig

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


class ScheduleTab(QWidget):
    config_changed = Signal()

    def __init__(self):
        super().__init__()

        self.enabled_check = QCheckBox("Bật lịch tự động")
        self.excel_edit = QLineEdit()
        self.image_folder_edit = QLineEdit()
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem("Hằng ngày", "daily")
        self.frequency_combo.addItem("Hằng tuần", "weekly")
        self.frequency_combo.addItem("Một lần theo ngày giờ", "once")
        self.frequency_combo.addItem("Custom cron", "custom")
        self.weekday_combo = QComboBox()
        self.weekday_combo.addItems(["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.run_at_edit = QDateTimeEdit()
        self.run_at_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.run_at_edit.setCalendarPopup(True)
        self.run_at_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.cron_edit = QLineEdit()
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

        self.next_run_label = QLabel("Chưa lên lịch")
        self.last_run_label = QLabel("Chưa chạy")

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

        form = QFormLayout()
        form.addRow("", self.enabled_check)
        form.addRow("File Excel", excel_row)
        form.addRow("Thư mục ảnh", image_row)
        form.addRow("Tần suất", self.frequency_combo)
        form.addRow("Thứ", self.weekday_combo)
        form.addRow("Giờ", self.time_edit)
        form.addRow("Ngày giờ chạy", self.run_at_edit)
        form.addRow("Cron", self.cron_edit)
        form.addRow("Ảnh tối đa mỗi bài", self.max_images_spin)
        form.addRow("Kích thước ảnh", image_size_row)
        form.addRow("Căn chỉnh ảnh", self.image_align_combo)
        form.addRow("Lần chạy kế tiếp", self.next_run_label)
        form.addRow("Lần chạy gần nhất", self.last_run_label)

        box = QGroupBox("Lịch tự động")
        box.setLayout(form)

        layout = QVBoxLayout(self)
        layout.addWidget(box)
        layout.addStretch(1)

        for widget in [
            self.enabled_check,
            self.excel_edit,
            self.image_folder_edit,
            self.frequency_combo,
            self.weekday_combo,
            self.time_edit,
            self.run_at_edit,
            self.cron_edit,
            self.max_images_spin,
            self.image_size_combo,
            self.image_align_combo,
        ]:
            signal = getattr(widget, "textChanged", None) or getattr(widget, "currentTextChanged", None)
            if signal:
                signal.connect(self.config_changed.emit)
        self.enabled_check.stateChanged.connect(self.config_changed.emit)
        self.time_edit.timeChanged.connect(self.config_changed.emit)
        self.run_at_edit.dateTimeChanged.connect(self.config_changed.emit)
        self.max_images_spin.valueChanged.connect(self.config_changed.emit)
        self.image_custom_width_spin.valueChanged.connect(self.config_changed.emit)
        self.frequency_combo.currentTextChanged.connect(self._update_mode_visibility)
        self._update_mode_visibility()

    def load_config(self, config: ScheduleConfig) -> None:
        self.enabled_check.setChecked(config.enabled)
        self.excel_edit.setText(config.excel_path)
        self.image_folder_edit.setText(config.image_folder)
        frequency_index = self.frequency_combo.findData(config.frequency)
        if frequency_index >= 0:
            self.frequency_combo.setCurrentIndex(frequency_index)
        self.weekday_combo.setCurrentText(config.weekday)
        parsed_time = QTime.fromString(config.time, "HH:mm")
        if parsed_time.isValid():
            self.time_edit.setTime(parsed_time)
        parsed_run_at = QDateTime.fromString(config.run_at, Qt.ISODate)
        if parsed_run_at.isValid():
            self.run_at_edit.setDateTime(parsed_run_at)
        elif config.frequency == "once":
            self.run_at_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.cron_edit.setText(config.cron_expression)
        self.max_images_spin.setValue(config.max_images_per_post)

        # Restore image display settings
        for i, (_label, value) in enumerate(_IMAGE_SIZE_OPTIONS):
            if value == config.image_display_size:
                self.image_size_combo.setCurrentIndex(i)
                break
        for i, (_label, value) in enumerate(_IMAGE_ALIGN_OPTIONS):
            if value == config.image_alignment:
                self.image_align_combo.setCurrentIndex(i)
                break
        self.image_custom_width_spin.setValue(config.image_custom_width)
        self._on_image_size_changed()

        self.last_run_label.setText(_status_text(config.last_run_at, config.last_result))
        self._update_mode_visibility()

    def to_config(self) -> ScheduleConfig:
        size_index = self.image_size_combo.currentIndex()
        display_size = _IMAGE_SIZE_OPTIONS[size_index][1] if size_index < len(_IMAGE_SIZE_OPTIONS) else "auto"
        align_index = self.image_align_combo.currentIndex()
        alignment = _IMAGE_ALIGN_OPTIONS[align_index][1] if align_index < len(_IMAGE_ALIGN_OPTIONS) else "aligncenter"
        return ScheduleConfig(
            enabled=self.enabled_check.isChecked(),
            excel_path=self.excel_edit.text().strip(),
            image_folder=self.image_folder_edit.text().strip(),
            frequency=self._frequency(),
            time=self.time_edit.time().toString("HH:mm"),
            run_at=self.run_at_edit.dateTime().toString(Qt.ISODate),
            weekday=self.weekday_combo.currentText(),
            cron_expression=self.cron_edit.text().strip(),
            max_images_per_post=self.max_images_spin.value(),
            image_alignment=alignment,
            image_display_size=display_size,
            image_custom_width=self.image_custom_width_spin.value(),
        )

    def set_next_run(self, value: str | None) -> None:
        self.next_run_label.setText(value or "Chưa lên lịch")

    def _choose_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel (*.xlsx *.xls)")
        if path:
            self.excel_edit.setText(path)

    def _choose_image_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục ảnh")
        if path:
            self.image_folder_edit.setText(path)

    def _update_mode_visibility(self) -> None:
        frequency = self._frequency()
        self.weekday_combo.setEnabled(frequency == "weekly")
        self.time_edit.setEnabled(frequency in {"daily", "weekly"})
        self.run_at_edit.setEnabled(frequency == "once")
        self.cron_edit.setEnabled(frequency == "custom")

    def _on_image_size_changed(self) -> None:
        """Show/hide custom width spin based on selected image size."""
        index = self.image_size_combo.currentIndex()
        size_value = _IMAGE_SIZE_OPTIONS[index][1] if index < len(_IMAGE_SIZE_OPTIONS) else "auto"
        self.image_custom_width_spin.setVisible(size_value == "custom")

    def _frequency(self) -> str:
        return self.frequency_combo.currentData() or self.frequency_combo.currentText()


def _status_text(last_run_at: str | None, last_result: str | None) -> str:
    if not last_run_at:
        return "Chưa chạy"
    return f"{last_run_at}: {last_result or ''}"

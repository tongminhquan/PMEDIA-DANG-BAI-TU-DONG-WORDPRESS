from __future__ import annotations

from PySide6.QtCore import QTime, Signal
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
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from wp_auto_poster_gui.core.scheduler_service import ScheduleConfig


class ScheduleTab(QWidget):
    config_changed = Signal()

    def __init__(self):
        super().__init__()

        self.enabled_check = QCheckBox("Bật lịch tự động")
        self.excel_edit = QLineEdit()
        self.image_folder_edit = QLineEdit()
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["daily", "weekly", "custom"])
        self.weekday_combo = QComboBox()
        self.weekday_combo.addItems(["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.cron_edit = QLineEdit()
        self.max_images_spin = QSpinBox()
        self.max_images_spin.setRange(0, 50)
        self.max_images_spin.setValue(5)
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

        form = QFormLayout()
        form.addRow("", self.enabled_check)
        form.addRow("File Excel", excel_row)
        form.addRow("Thư mục ảnh", image_row)
        form.addRow("Tần suất", self.frequency_combo)
        form.addRow("Thứ", self.weekday_combo)
        form.addRow("Giờ", self.time_edit)
        form.addRow("Cron", self.cron_edit)
        form.addRow("Ảnh tối đa mỗi bài", self.max_images_spin)
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
            self.cron_edit,
            self.max_images_spin,
        ]:
            signal = getattr(widget, "textChanged", None) or getattr(widget, "currentTextChanged", None)
            if signal:
                signal.connect(self.config_changed.emit)
        self.enabled_check.stateChanged.connect(self.config_changed.emit)
        self.time_edit.timeChanged.connect(self.config_changed.emit)
        self.max_images_spin.valueChanged.connect(self.config_changed.emit)
        self.frequency_combo.currentTextChanged.connect(self._update_mode_visibility)
        self._update_mode_visibility()

    def load_config(self, config: ScheduleConfig) -> None:
        self.enabled_check.setChecked(config.enabled)
        self.excel_edit.setText(config.excel_path)
        self.image_folder_edit.setText(config.image_folder)
        self.frequency_combo.setCurrentText(config.frequency)
        self.weekday_combo.setCurrentText(config.weekday)
        parsed_time = QTime.fromString(config.time, "HH:mm")
        if parsed_time.isValid():
            self.time_edit.setTime(parsed_time)
        self.cron_edit.setText(config.cron_expression)
        self.max_images_spin.setValue(config.max_images_per_post)
        self.last_run_label.setText(_status_text(config.last_run_at, config.last_result))
        self._update_mode_visibility()

    def to_config(self) -> ScheduleConfig:
        return ScheduleConfig(
            enabled=self.enabled_check.isChecked(),
            excel_path=self.excel_edit.text().strip(),
            image_folder=self.image_folder_edit.text().strip(),
            frequency=self.frequency_combo.currentText(),
            time=self.time_edit.time().toString("HH:mm"),
            weekday=self.weekday_combo.currentText(),
            cron_expression=self.cron_edit.text().strip(),
            max_images_per_post=self.max_images_spin.value(),
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
        frequency = self.frequency_combo.currentText()
        self.weekday_combo.setEnabled(frequency == "weekly")
        self.time_edit.setEnabled(frequency in {"daily", "weekly"})
        self.cron_edit.setEnabled(frequency == "custom")


def _status_text(last_run_at: str | None, last_result: str | None) -> str:
    if not last_run_at:
        return "Chưa chạy"
    return f"{last_run_at}: {last_result or ''}"

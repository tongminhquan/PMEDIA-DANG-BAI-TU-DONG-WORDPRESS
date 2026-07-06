from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
)


class AdvancedSettingsDialog(QDialog):
    def __init__(self, delay_seconds: int = 0, retry_count: int = 3, timeout_seconds: int = 30):
        super().__init__()
        self.setWindowTitle("Cài đặt nâng cao")

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 3600)
        self.delay_spin.setValue(delay_seconds)
        self.delay_spin.setSuffix(" giây")

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setValue(retry_count)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(timeout_seconds)
        self.timeout_spin.setSuffix(" giây")

        form = QFormLayout()
        form.addRow("Delay giữa bài", self.delay_spin)
        form.addRow("Số lần retry", self.retry_spin)
        form.addRow("Timeout request", self.timeout_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[int, int, int]:
        return self.delay_spin.value(), self.retry_spin.value(), self.timeout_spin.value()

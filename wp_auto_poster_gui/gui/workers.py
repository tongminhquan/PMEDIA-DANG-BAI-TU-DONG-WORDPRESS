from __future__ import annotations

from threading import Event

from PySide6.QtCore import QThread, Signal

from wp_auto_poster_gui.core.models import PosterOptions, WordPressConfig
from wp_auto_poster_gui.core.poster_service import publish_from_excel
from wp_auto_poster_gui.core.wp_client import WordPressClient


class ConnectionTestWorker(QThread):
    finished_with_result = Signal(bool, str)

    def __init__(self, config: WordPressConfig):
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            ok, message = WordPressClient(self.config).test_connection()
            self.finished_with_result.emit(ok, message)
        except Exception as exc:
            self.finished_with_result.emit(False, str(exc))


class PosterWorker(QThread):
    progress = Signal(str)
    completed = Signal(object, object)

    def __init__(
        self,
        excel_path: str,
        image_folder: str | None,
        config: WordPressConfig,
        options: PosterOptions,
        stop_event: Event,
    ):
        super().__init__()
        self.excel_path = excel_path
        self.image_folder = image_folder
        self.config = config
        self.options = options
        self.stop_event = stop_event

    def run(self) -> None:
        try:
            results, orphan_files = publish_from_excel(
                self.excel_path,
                self.image_folder,
                self.config,
                self.options,
                progress_callback=self.progress.emit,
                stop_event=self.stop_event,
            )
            self.completed.emit(results, orphan_files)
        except Exception as exc:
            self.progress.emit(f"Lỗi: {exc}")
            self.completed.emit([], [])

from __future__ import annotations

from pathlib import Path
import sys


APP_NAME = "PMEDIA-Đăng bài tự động wordpress"


def resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return base_path / relative_path


APP_ICON_PATH = resource_path("wp_auto_poster_gui/assets/pmedia_logo.ico")

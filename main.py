from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication, QMessageBox
        from wp_auto_poster_gui.app_info import APP_ICON_PATH, APP_NAME
        from wp_auto_poster_gui.gui.main_window import MainWindow
    except ImportError as exc:
        print(f"Missing GUI dependency: {exc}")
        print("Install dependencies with: python -m pip install -r requirements.txt")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    try:
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(None, APP_NAME, str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

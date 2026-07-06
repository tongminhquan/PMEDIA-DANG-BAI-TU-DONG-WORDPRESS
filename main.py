from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from wp_auto_poster_gui.gui.main_window import MainWindow
    except ImportError as exc:
        print(f"Missing GUI dependency: {exc}")
        print("Install dependencies with: python -m pip install -r requirements.txt")
        return 1

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    try:
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(None, "WordPress Auto Poster", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

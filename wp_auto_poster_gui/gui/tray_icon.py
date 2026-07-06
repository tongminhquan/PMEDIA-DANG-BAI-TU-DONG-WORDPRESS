from __future__ import annotations

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from wp_auto_poster_gui.app_info import APP_NAME


def create_tray_icon(parent, icon: QIcon | None = None) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(icon or parent.windowIcon(), parent)
    tray.setToolTip(APP_NAME)
    menu = QMenu(parent)

    open_action = QAction("Mở ứng dụng", parent)
    open_action.triggered.connect(parent.show_normal_from_tray)
    quit_action = QAction("Thoát hẳn", parent)
    quit_action.triggered.connect(parent.quit_application)

    menu.addAction(open_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: parent.show_normal_from_tray() if reason == QSystemTrayIcon.DoubleClick else None)
    tray.show()
    return tray

"""QApplication setup with HiDPI handling."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication


def create_app(argv: list[str] | None = None) -> QApplication:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("YoutubeDownloader")
    app.setOrganizationName("YoutubeDownloader")
    app.setStyle("Fusion")
    return app

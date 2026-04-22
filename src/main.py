"""Entry point for the Windows YouTube Downloader."""

from __future__ import annotations

import sys

from src.app import create_app
from src.ui.main_window import MainWindow


def main() -> int:
    app = create_app(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

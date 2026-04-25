"""Dialog for entering a URL and selecting quality/format."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from src.core import settings
from src.core.downloader import FORMAT_CHOICES, QUALITY_CHOICES
from src.core.url_utils import parse


_QUALITY_LABEL = {
    "best": "En yüksek (4K/8K dahil otomatik)",
    "1080p": "1080p",
    "720p": "720p",
    "480p": "480p",
    "360p": "360p",
    "audio": "Sadece ses",
}


class AddDialog(QDialog):
    def __init__(self, parent=None, prefilled_url: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("URL Ekle")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.url_edit = QLineEdit(prefilled_url)
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=... veya /shorts/... veya /playlist?list=...")

        self.quality = QComboBox()
        for key in QUALITY_CHOICES:
            self.quality.addItem(_QUALITY_LABEL.get(key, key), key)
        self.quality.setCurrentIndex(max(0, QUALITY_CHOICES.index(settings.default_quality())))

        self.container = QComboBox()
        for fmt in FORMAT_CHOICES:
            self.container.addItem(fmt.upper(), fmt)
        self.container.setCurrentIndex(max(0, FORMAT_CHOICES.index(settings.default_format())))

        self.kind_label = QLabel("Tür: -")
        self.kind_label.setStyleSheet("color: #555;")

        form = QFormLayout()
        form.addRow("URL:", self.url_edit)
        form.addRow("Kalite:", self.quality)
        form.addRow("Format:", self.container)
        form.addRow(self.kind_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignRight)

        self.url_edit.textChanged.connect(self._update_kind)
        self._update_kind(prefilled_url)

    def _update_kind(self, text: str) -> None:
        kind = parse(text).kind if text.strip() else "unknown"
        labels = {
            "video": "Video",
            "shorts": "Shorts",
            "playlist": "Oynatma Listesi",
            "mixed": "Video + Oynatma Listesi",
            "unknown": "—",
        }
        self.kind_label.setText(f"Tür: {labels.get(kind, kind)}")

    # Convenience ------------------------------------------------------
    def url(self) -> str:
        return self.url_edit.text().strip()

    def selected_quality(self) -> str:
        return self.quality.currentData() or "best"

    def selected_format(self) -> str:
        return self.container.currentData() or "mp4"

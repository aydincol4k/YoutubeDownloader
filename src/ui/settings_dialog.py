"""Application settings dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.core import settings


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.dir_edit = QLineEdit(str(settings.download_dir()))
        browse = QPushButton("Gözat...")
        browse.clicked.connect(self._pick_dir)

        dir_row = QHBoxLayout()
        dir_row.addWidget(self.dir_edit, stretch=1)
        dir_row.addWidget(browse)

        self.concurrency = QSpinBox()
        self.concurrency.setRange(1, 10)
        self.concurrency.setValue(settings.concurrent_downloads())

        form = QFormLayout()
        form.addRow("İndirme klasörü:", dir_row)
        form.addRow("Eşzamanlı indirme:", self.concurrency)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _pick_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "İndirme klasörü", self.dir_edit.text())
        if chosen:
            self.dir_edit.setText(chosen)

    def _save(self) -> None:
        path = Path(self.dir_edit.text()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        settings.set_download_dir(path)
        settings.set_concurrent_downloads(self.concurrency.value())
        self.accept()

"""Dialog that shows a playlist and lets the user select videos to download."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from src.core.playlist import PlaylistEntry, PlaylistInfo


def _format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "--:--"
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class PlaylistDialog(QDialog):
    def __init__(self, info: PlaylistInfo, parent=None) -> None:
        super().__init__(parent)
        self.info = info
        self.setWindowTitle("Oynatma Listesi")
        self.setModal(True)
        self.resize(640, 520)

        header = QLabel(
            f"<b>{info.title}</b><br>"
            f"{len(info.entries)} video · toplam {_format_duration(info.total_duration)}"
        )
        header.setTextFormat(Qt.TextFormat.RichText)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Başlığa göre filtrele...")
        self.search.textChanged.connect(self._apply_filter)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for idx, entry in enumerate(info.entries, start=1):
            item = QListWidgetItem(
                f"{idx:>3}. {entry.title}   ·   {_format_duration(entry.duration)}"
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.list_widget.addItem(item)

        select_all = QPushButton("Tümünü Seç")
        select_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        select_none = QPushButton("Seçimi Kaldır")
        select_none.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))

        actions = QHBoxLayout()
        actions.addWidget(select_all)
        actions.addWidget(select_none)
        actions.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Seçilenleri İndir")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self.search)
        layout.addLayout(actions)
        layout.addWidget(self.list_widget, stretch=1)
        layout.addWidget(buttons)

    def _set_all(self, state: Qt.CheckState) -> None:
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(state)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            entry: PlaylistEntry = item.data(Qt.ItemDataRole.UserRole)
            item.setHidden(bool(needle) and needle not in entry.title.lower())

    def selected_entries(self) -> list[PlaylistEntry]:
        out: list[PlaylistEntry] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                out.append(item.data(Qt.ItemDataRole.UserRole))
        return out

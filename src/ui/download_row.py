"""Single download row widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.downloader import DownloadJob, DownloadWorker, Progress


def _format_bytes(n: float | int | None) -> str:
    if not n:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    idx = 0
    val = float(n)
    while val >= 1024 and idx < len(units) - 1:
        val /= 1024
        idx += 1
    return f"{val:.1f} {units[idx]}"


def _format_eta(seconds: int | None) -> str:
    if seconds is None or seconds < 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class DownloadRow(QWidget):
    """Visual representation of a single download."""

    cancelled = Signal(object)  # emits self
    finished = Signal(object)  # emits self

    def __init__(self, job: DownloadJob, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.job = job
        self._worker: DownloadWorker | None = None
        self._build_ui()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(10)

        info_box = QVBoxLayout()
        info_box.setSpacing(2)

        label_text = self.job.title_hint or self.job.url
        self.title_label = QLabel(label_text)
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.status_label = QLabel("Queued")
        self.status_label.setStyleSheet("color: #555;")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)

        info_box.addWidget(self.title_label)
        info_box.addWidget(self.progress)
        info_box.addWidget(self.status_label)

        outer.addLayout(info_box, stretch=1)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        outer.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignTop)

    # Worker lifecycle -------------------------------------------------
    def attach(self, worker: DownloadWorker) -> None:
        self._worker = worker
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.failed.connect(self._on_failed)

    def _on_cancel_clicked(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.status_label.setText("Cancelling...")
        else:
            self.cancelled.emit(self)

    # Slots ------------------------------------------------------------
    def _on_progress(self, p: Progress) -> None:
        if p.title and p.title != self.job.title_hint:
            self.title_label.setText(p.title)
        self.progress.setValue(int(p.percent))
        if p.status == "downloading":
            speed = f"{_format_bytes(p.speed)}/s" if p.speed else "-- B/s"
            of_total = _format_bytes(p.total_bytes) if p.total_bytes else "?"
            self.status_label.setText(
                f"{_format_bytes(p.downloaded_bytes)} / {of_total}  ·  {speed}  ·  ETA {_format_eta(p.eta)}"
            )
        elif p.status == "finished":
            self.status_label.setText("Post-processing...")

    def _on_finished(self, path: str) -> None:
        self.progress.setValue(100)
        self.status_label.setText(f"Done · {path}" if path else "Done")
        self.cancel_btn.setText("Remove")
        self.finished.emit(self)

    def _on_failed(self, message: str) -> None:
        self.status_label.setText(f"Failed: {message}")
        self.status_label.setStyleSheet("color: #b00020;")
        self.cancel_btn.setText("Remove")
        self.finished.emit(self)

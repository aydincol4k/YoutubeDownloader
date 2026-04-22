"""Main application window."""

from __future__ import annotations

import os
import sys
from collections import deque
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QAction, QGuiApplication, QResizeEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core import playlist as playlist_mod
from src.core import settings
from src.core.downloader import DownloadJob, DownloadWorker
from src.core.url_utils import parse
from src.ui.add_dialog import AddDialog
from src.ui.download_row import DownloadRow
from src.ui.playlist_dialog import PlaylistDialog
from src.ui.settings_dialog import SettingsDialog


class _PlaylistFetchWorker(QThread):
    fetched = Signal(object)
    failed = Signal(str)

    def __init__(self, url: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.url = url

    def run(self) -> None:
        try:
            info = playlist_mod.fetch(self.url)
            self.fetched.emit(info)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    _COMPACT_WIDTH = 700

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self._rows: list[DownloadRow] = []
        self._workers: list[DownloadWorker] = []
        self._queue: deque[tuple[DownloadRow, DownloadWorker]] = deque()
        self._active = 0
        self._playlist_workers: list[_PlaylistFetchWorker] = []
        self._build_ui()
        self._size_to_screen()

    # UI construction --------------------------------------------------
    def _build_ui(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        self._toolbar = toolbar

        add_action = QAction("URL Ekle", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self._on_add_url)
        toolbar.addAction(add_action)

        paste_action = QAction("Panodan Yapıştır", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self._on_paste)
        toolbar.addAction(paste_action)

        toolbar.addSeparator()

        open_folder = QAction("İndirme Klasörünü Aç", self)
        open_folder.triggered.connect(self._open_download_dir)
        toolbar.addAction(open_folder)

        settings_action = QAction("Ayarlar", self)
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)

        # Central area: scrollable list of download rows
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)

        self._list_host = QWidget()
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch(1)

        self._empty_label = QLabel("Henüz indirme yok. Bir YouTube URL'i eklemek için Ctrl+N'e basın.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #888; padding: 40px;")
        self._list_layout.insertWidget(0, self._empty_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._list_host)
        central_layout.addWidget(scroll, stretch=1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._update_status()
        self.setMinimumSize(800, 500)

    def _size_to_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            self.resize(1100, 700)
            return
        geo = screen.availableGeometry()
        w = max(800, int(geo.width() * 0.7))
        h = max(500, int(geo.height() * 0.7))
        self.resize(w, h)
        frame = self.frameGeometry()
        frame.moveCenter(geo.center())
        self.move(frame.topLeft())

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 (Qt naming)
        super().resizeEvent(event)
        compact = event.size().width() < self._COMPACT_WIDTH
        style = (
            Qt.ToolButtonStyle.ToolButtonIconOnly
            if compact
            else Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._toolbar.setToolButtonStyle(style)

    # Slots ------------------------------------------------------------
    def _on_add_url(self) -> None:
        clipboard = QGuiApplication.clipboard().text().strip()
        prefilled = clipboard if parse(clipboard).kind != "unknown" else ""
        self._open_add_dialog(prefilled)

    def _on_paste(self) -> None:
        text = QGuiApplication.clipboard().text().strip()
        self._open_add_dialog(text)

    def _open_add_dialog(self, prefilled: str) -> None:
        dlg = AddDialog(self, prefilled_url=prefilled)
        if dlg.exec() != AddDialog.DialogCode.Accepted:
            return
        url = dlg.url()
        quality = dlg.selected_quality()
        container = dlg.selected_format()
        if not url:
            return
        parsed = parse(url)
        if parsed.kind == "unknown":
            QMessageBox.warning(self, "Geçersiz URL", "Bu URL geçerli bir YouTube bağlantısı değil.")
            return
        if parsed.kind == "playlist":
            self._start_playlist_flow(parsed.canonical, quality, container)
            return
        if parsed.kind == "mixed":
            choice = QMessageBox.question(
                self,
                "Video + Oynatma Listesi",
                "Bu bağlantı hem bir video hem de oynatma listesi içeriyor.\n\n"
                "Tüm oynatma listesini indirmek ister misin?\n"
                "(Hayır = sadece bu video)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice == QMessageBox.StandardButton.Yes:
                playlist_url = f"https://www.youtube.com/playlist?list={parsed.playlist_id}"
                self._start_playlist_flow(playlist_url, quality, container)
                return
            url = f"https://www.youtube.com/watch?v={parsed.video_id}"
        else:
            url = parsed.canonical
        self._enqueue_job(
            DownloadJob(
                url=url,
                output_dir=settings.download_dir(),
                quality=quality,
                container=container,
                title_hint=url,
            )
        )

    def _start_playlist_flow(self, url: str, quality: str, container: str) -> None:
        self.statusBar().showMessage("Oynatma listesi yükleniyor...")
        worker = _PlaylistFetchWorker(url, self)
        worker.fetched.connect(lambda info: self._on_playlist_fetched(info, quality, container))
        worker.failed.connect(self._on_playlist_failed)
        worker.finished.connect(lambda: self._cleanup_playlist_worker(worker))
        self._playlist_workers.append(worker)
        worker.start()

    def _cleanup_playlist_worker(self, worker: _PlaylistFetchWorker) -> None:
        if worker in self._playlist_workers:
            self._playlist_workers.remove(worker)
        worker.deleteLater()

    def _on_playlist_fetched(self, info, quality: str, container: str) -> None:
        self.statusBar().clearMessage()
        if not info.entries:
            QMessageBox.information(self, "Boş Liste", "Oynatma listesi boş veya erişilemiyor.")
            return
        dlg = PlaylistDialog(info, self)
        if dlg.exec() != PlaylistDialog.DialogCode.Accepted:
            return
        chosen = dlg.selected_entries()
        if not chosen:
            return
        subdir = info.title or "Playlist"
        for entry in chosen:
            self._enqueue_job(
                DownloadJob(
                    url=entry.url,
                    output_dir=settings.download_dir(),
                    quality=quality,
                    container=container,
                    playlist_subdir=subdir,
                    title_hint=entry.title,
                )
            )

    def _on_playlist_failed(self, message: str) -> None:
        self.statusBar().clearMessage()
        QMessageBox.warning(self, "Oynatma Listesi Hatası", message)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()
        self._update_status()

    def _open_download_dir(self) -> None:
        path = settings.download_dir()
        path.mkdir(parents=True, exist_ok=True)
        self._reveal(path)

    @staticmethod
    def _reveal(path: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except OSError:
            pass

    # Queue ------------------------------------------------------------
    def _enqueue_job(self, job: DownloadJob) -> None:
        row = DownloadRow(job)
        worker = DownloadWorker(job)
        row.attach(worker)
        row.cancelled.connect(self._remove_row)
        row.finished.connect(self._on_row_finished)
        self._add_row_widget(row)
        self._rows.append(row)
        self._workers.append(worker)
        self._queue.append((row, worker))
        self._pump_queue()
        self._update_status()

    def _add_row_widget(self, row: DownloadRow) -> None:
        if self._empty_label.isVisible():
            self._empty_label.setVisible(False)
        # Insert before the trailing stretch (last item)
        insert_at = self._list_layout.count() - 1
        self._list_layout.insertWidget(insert_at, row)

    def _pump_queue(self) -> None:
        limit = settings.concurrent_downloads()
        while self._active < limit and self._queue:
            _, worker = self._queue.popleft()
            self._active += 1
            worker.start()

    def _on_row_finished(self, row: DownloadRow) -> None:
        self._active = max(0, self._active - 1)
        self._pump_queue()
        self._update_status()

    def _remove_row(self, row: DownloadRow) -> None:
        if row in self._rows:
            self._rows.remove(row)
        self._list_layout.removeWidget(row)
        row.deleteLater()
        if not self._rows:
            self._empty_label.setVisible(True)
        self._update_status()

    def _update_status(self) -> None:
        active = sum(1 for w in self._workers if w.isRunning())
        queued = len(self._queue)
        done = sum(1 for r in self._rows if r.progress.value() >= 100)
        self.statusBar().showMessage(
            f"Aktif: {active}  ·  Sırada: {queued}  ·  Tamamlanan: {done}  ·  Hedef: {settings.download_dir()}"
        )

    # Cleanup ----------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802
        for worker in self._workers:
            if worker.isRunning():
                worker.cancel()
        for worker in self._workers:
            worker.wait(2000)
        super().closeEvent(event)

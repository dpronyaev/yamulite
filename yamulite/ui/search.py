from __future__ import annotations

from PyQt6.QtCore import QEvent, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from .. import settings as user_settings
from ..api import Api
from ..workers import run
from .widgets import (
    SimpleList, TrackList, fmt_album, fmt_artist,
)


class SearchPage(QWidget):
    track_play_requested = pyqtSignal(list, int)  # tracks, start_index
    album_opened = pyqtSignal(object)
    artist_opened = pyqtSignal(object)
    likes_changed = pyqtSignal()

    def __init__(self, api: Api):
        super().__init__()
        self.api = api
        self._query: str = ""
        self._page: int = 0
        self._totals = {"tracks": 0, "albums": 0, "artists": 0}

        top = QHBoxLayout()
        self.edit = QComboBox()
        self.edit.setEditable(True)
        self.edit.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.edit.setMaxVisibleItems(user_settings.MAX_SEARCH_HISTORY)
        self.edit.lineEdit().setPlaceholderText(
            "Поиск трека, исполнителя или альбома…"
        )
        self.edit.lineEdit().returnPressed.connect(self._do_search)
        self.edit.activated.connect(self._on_history_activated)
        self._reload_history()
        self.edit.setCurrentText("")
        self.edit.lineEdit().installEventFilter(self)
        btn = QPushButton("Найти")
        btn.clicked.connect(self._do_search)
        top.addWidget(self.edit, 1)
        top.addWidget(btn)

        self.tabs = QTabWidget()
        self.tracks_list = TrackList(api)
        self.albums_list = SimpleList(fmt_album)
        self.artists_list = SimpleList(fmt_artist)

        self.tabs.addTab(self.tracks_list, "Треки")
        self.tabs.addTab(self.albums_list, "Альбомы")
        self.tabs.addTab(self.artists_list, "Исполнители")

        self.more_btn = QPushButton("Показать ещё")
        self.more_btn.setVisible(False)
        self.more_btn.clicked.connect(self._load_more)

        self.tracks_list.play_requested.connect(
            lambda i: self.track_play_requested.emit(self.tracks_list.tracks(), i)
        )
        self.tracks_list.likes_changed.connect(self.likes_changed.emit)
        self.albums_list.item_activated.connect(self.album_opened.emit)
        self.artists_list.item_activated.connect(self.artist_opened.emit)

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addWidget(self.tabs, 1)
        root.addWidget(self.more_btn)

    def set_liked_ids(self, ids: set) -> None:
        self.tracks_list.set_liked_ids(ids)

    def _do_search(self) -> None:
        q = self.edit.currentText().strip()
        if not q:
            return
        self._query = q
        self._page = 0
        self._totals = {"tracks": 0, "albums": 0, "artists": 0}
        self.more_btn.setEnabled(False)
        user_settings.add_search_history(q)
        self._reload_history(keep_text=q)
        run(self.api.search, q, "all", page=0, on_result=self._on_first_result)

    def _on_history_activated(self, _idx: int) -> None:
        self._do_search()

    def _reload_history(self, keep_text: str | None = None) -> None:
        current = keep_text if keep_text is not None else self.edit.currentText()
        self.edit.blockSignals(True)
        self.edit.clear()
        self.edit.addItems(user_settings.get_search_history())
        self.edit.setCurrentText(current)
        self.edit.blockSignals(False)

    def eventFilter(self, obj, event):
        if obj is self.edit.lineEdit() and event.type() == QEvent.Type.MouseButtonPress:
            if self.edit.count() > 0 and not self.edit.view().isVisible():
                QTimer.singleShot(0, self.edit.showPopup)
        return super().eventFilter(obj, event)

    def _load_more(self) -> None:
        self._page += 1
        self.more_btn.setEnabled(False)
        run(self.api.search, self._query, "all", page=self._page,
            on_result=self._on_more_result)

    # --- result handlers --------------------------------------------------
    def _extract(self, res):
        tracks = list((res.tracks.results if res and res.tracks else []) or [])
        albums = list((res.albums.results if res and res.albums else []) or [])
        artists = list((res.artists.results if res and res.artists else []) or [])
        self._totals = {
            "tracks": (res.tracks.total if res and res.tracks else 0) or 0,
            "albums": (res.albums.total if res and res.albums else 0) or 0,
            "artists": (res.artists.total if res and res.artists else 0) or 0,
        }
        return tracks, albums, artists

    def _on_first_result(self, res) -> None:
        tracks, albums, artists = self._extract(res)
        self.tracks_list.set_tracks(tracks)
        self.albums_list.set_items(albums)
        self.artists_list.set_items(artists)
        self._update_more_visibility()

    def _on_more_result(self, res) -> None:
        tracks, albums, artists = self._extract(res)
        if tracks:
            self.tracks_list.append_tracks(tracks)
        if albums:
            self.albums_list.append_items(albums)
        if artists:
            self.artists_list.append_items(artists)
        if not (tracks or albums or artists):
            self.more_btn.setVisible(False)
            return
        self._update_more_visibility()

    def _update_more_visibility(self) -> None:
        shown_tracks = len(self.tracks_list.tracks())
        shown_albums = len(self.albums_list.items())
        shown_artists = len(self.artists_list.items())
        has_more = (
            shown_tracks < self._totals["tracks"]
            or shown_albums < self._totals["albums"]
            or shown_artists < self._totals["artists"]
        )
        self.more_btn.setVisible(has_more)
        self.more_btn.setEnabled(has_more)

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from ..api import Api
from ..workers import run
from .widgets import SimpleList, TrackList, fmt_playlist


class LibraryPage(QWidget):
    track_play_requested = pyqtSignal(list, int)
    playlist_opened = pyqtSignal(object)

    def __init__(self, api: Api):
        super().__init__()
        self.api = api

        self.tabs = QTabWidget()
        self.liked = TrackList(api)
        self.playlists = SimpleList(fmt_playlist)

        self.tabs.addTab(self.liked, "Мне нравится")
        self.tabs.addTab(self.playlists, "Плейлисты")

        self.liked.play_requested.connect(
            lambda i: self.track_play_requested.emit(self.liked.tracks(), i)
        )
        self.playlists.item_activated.connect(self.playlist_opened.emit)

        root = QVBoxLayout(self)
        root.addWidget(self.tabs, 1)

    def set_liked_ids(self, ids: set) -> None:
        self.liked.set_liked_ids(ids)

    def refresh(self) -> None:
        run(self.api.liked_tracks, on_result=self.liked.set_tracks)
        run(self.api.user_playlists, on_result=self.playlists.set_items)

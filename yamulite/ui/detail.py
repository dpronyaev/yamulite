"""Detail pages: album / artist / playlist content."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ..api import Api
from ..workers import run
from .widgets import TrackList


class _TracksPage(QWidget):
    track_play_requested = pyqtSignal(list, int)
    likes_changed = pyqtSignal()

    def __init__(self, api: Api, title: str):
        super().__init__()
        self.api = api
        self.title_label = QLabel(f"<h2>{title}</h2>")
        self.title_label.setTextFormat(Qt.TextFormat.RichText)
        self.back_btn = QPushButton("← Назад")
        self.tracks = TrackList(api)
        self.tracks.play_requested.connect(
            lambda i: self.track_play_requested.emit(self.tracks.tracks(), i)
        )
        self.tracks.likes_changed.connect(self.likes_changed.emit)
        self.more_btn = QPushButton("Показать ещё")
        self.more_btn.setVisible(False)

        v = QVBoxLayout(self)
        v.addWidget(self.back_btn)
        v.addWidget(self.title_label)
        v.addWidget(self.tracks, 1)
        v.addWidget(self.more_btn)

    def set_liked_ids(self, ids: set) -> None:
        self.tracks.set_liked_ids(ids)


class AlbumPage(_TracksPage):
    def load(self, album) -> None:
        title = f"{album.title}"
        artists = ", ".join(a.name for a in (album.artists or []) if a and a.name)
        if artists:
            title = f"{album.title} — {artists}"
        self.title_label.setText(f"<h2>{title}</h2>")
        self.more_btn.setVisible(False)
        run(self.api.album_tracks, album.id, on_result=self.tracks.set_tracks)


class ArtistPage(_TracksPage):
    PAGE_SIZE = 50

    def __init__(self, api: Api, title: str):
        super().__init__(api, title)
        self._artist_id: int | None = None
        self._page: int = 0
        self.more_btn.clicked.connect(self._load_more)

    def load(self, artist) -> None:
        self.title_label.setText(f"<h2>{artist.name}</h2>")
        self._artist_id = artist.id
        self._page = 0
        self.tracks.set_tracks([])
        self.more_btn.setVisible(False)
        self.more_btn.setEnabled(False)
        run(
            self.api.artist_tracks_page, artist.id, 0, self.PAGE_SIZE,
            on_result=self._on_page,
        )

    def _load_more(self) -> None:
        if self._artist_id is None:
            return
        self._page += 1
        self.more_btn.setEnabled(False)
        run(
            self.api.artist_tracks_page, self._artist_id, self._page, self.PAGE_SIZE,
            on_result=self._on_page,
        )

    def _on_page(self, result) -> None:
        tracks, has_more = result
        self.tracks.append_tracks(list(tracks))
        self.more_btn.setVisible(has_more)
        self.more_btn.setEnabled(has_more)


class PlaylistPage(_TracksPage):
    def load(self, playlist) -> None:
        self.title_label.setText(f"<h2>{playlist.title}</h2>")
        self.more_btn.setVisible(False)
        run(self.api.playlist_tracks, playlist, on_result=self.tracks.set_tracks)

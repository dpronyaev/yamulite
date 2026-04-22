from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout, QListWidget, QMainWindow, QMessageBox, QStackedWidget,
    QStatusBar, QVBoxLayout, QWidget,
)

from ..api import Api
from ..auth import clear_token
from ..player import Player
from ..workers import run
from .detail import AlbumPage, ArtistPage, PlaylistPage
from .library import LibraryPage
from .player_bar import PlayerBar
from .search import SearchPage


SECTIONS = ["Поиск", "Мне нравится и плейлисты"]


class MainWindow(QMainWindow):
    def __init__(self, token: str):
        super().__init__()
        self.setWindowTitle("YAMULITE")
        self.resize(1000, 680)

        self.api = Api(token)
        self.player = Player(self.api)
        self._liked_ids: set = set()

        # sidebar
        self.sidebar = QListWidget()
        self.sidebar.addItems(SECTIONS)
        self.sidebar.setFixedWidth(200)
        self.sidebar.currentRowChanged.connect(self._on_section_changed)

        # pages
        self.stack = QStackedWidget()
        self.search_page = SearchPage(self.api)
        self.library_page = LibraryPage(self.api)
        self.album_page = AlbumPage(self.api, "")
        self.artist_page = ArtistPage(self.api, "")
        self.playlist_page = PlaylistPage(self.api, "")

        for p in (self.search_page, self.library_page,
                  self.album_page, self.artist_page, self.playlist_page):
            self.stack.addWidget(p)

        # wiring
        self.search_page.track_play_requested.connect(self._play)
        self.search_page.album_opened.connect(self._open_album)
        self.search_page.artist_opened.connect(self._open_artist)
        self.library_page.track_play_requested.connect(self._play)
        self.library_page.playlist_opened.connect(self._open_playlist)

        for page in (self.album_page, self.artist_page, self.playlist_page):
            page.track_play_requested.connect(self._play)
            page.back_btn.clicked.connect(lambda _=False: self.stack.setCurrentIndex(
                0 if self.sidebar.currentRow() == 0 else 1
            ))

        # player bar
        self.player_bar = PlayerBar(self.player)

        top = QWidget()
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.addWidget(self.sidebar)
        top_lay.addWidget(self.stack, 1)

        root = QWidget()
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(top, 1)
        v.addWidget(self.player_bar)
        self.setCentralWidget(root)

        sb = QStatusBar()
        self.setStatusBar(sb)

        # keyboard: Space -> play/pause
        sp = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        sp.activated.connect(self.player.toggle)

        # initial
        self.sidebar.setCurrentRow(0)
        self._refresh_likes_and_library()
        run(self.api.account_name, on_result=lambda n: sb.showMessage(f"Вы вошли как {n}"))

        # logout via menu
        file_menu = self.menuBar().addMenu("Файл")
        logout_act = file_menu.addAction("Выйти из аккаунта")
        logout_act.triggered.connect(self._logout)

    # --- navigation -------------------------------------------------------
    def _on_section_changed(self, row: int) -> None:
        if row == 0:
            self.stack.setCurrentWidget(self.search_page)
        elif row == 1:
            self.stack.setCurrentWidget(self.library_page)

    def _open_album(self, album) -> None:
        self.album_page.set_liked_ids(self._liked_ids)
        self.album_page.load(album)
        self.stack.setCurrentWidget(self.album_page)

    def _open_artist(self, artist) -> None:
        self.artist_page.set_liked_ids(self._liked_ids)
        self.artist_page.load(artist)
        self.stack.setCurrentWidget(self.artist_page)

    def _open_playlist(self, playlist) -> None:
        self.playlist_page.set_liked_ids(self._liked_ids)
        self.playlist_page.load(playlist)
        self.stack.setCurrentWidget(self.playlist_page)

    # --- playback --------------------------------------------------------
    def _play(self, tracks, start_index: int) -> None:
        if not tracks:
            return
        self.player.set_queue(tracks, start_index)

    # --- library ---------------------------------------------------------
    def _refresh_likes_and_library(self) -> None:
        def fetch_ids():
            likes = self.api.client.users_likes_tracks()
            if not likes:
                return set()
            return {str(t.track_id or t.id) for t in likes.tracks}
        run(fetch_ids, on_result=self._apply_liked_ids)
        self.library_page.refresh()

    def _apply_liked_ids(self, ids: set) -> None:
        self._liked_ids = ids
        for p in (self.search_page, self.library_page,
                  self.album_page, self.artist_page, self.playlist_page):
            p.set_liked_ids(ids)

    # --- logout ----------------------------------------------------------
    def _logout(self) -> None:
        btn = QMessageBox.question(self, "YAMULITE", "Выйти из аккаунта?")
        if btn != QMessageBox.StandardButton.Yes:
            return
        clear_token()
        self.player.stop()
        self.close()

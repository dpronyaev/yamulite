"""Reusable widgets: track row list, item cards."""
from __future__ import annotations

from typing import Callable, List, Optional

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QVBoxLayout, QWidget,
)
from yandex_music import Album, Artist, Track

from ..api import Api
from ..covers import cover_uri_for, download_cover
from ..workers import cover_pool, run


def _artists_str(track: Track) -> str:
    return ", ".join(a.name for a in (track.artists or []) if a and a.name) or "—"


def _fmt_duration(ms: Optional[int]) -> str:
    if not ms:
        return ""
    s = int(ms) // 1000
    return f"{s // 60}:{s % 60:02d}"


class TrackRow(QWidget):
    COVER_SIZE = 40  # UI size; download size is the nearest supported (50)

    play_clicked = pyqtSignal(int)       # index in list
    like_toggled = pyqtSignal(object, bool)  # track_id, new_state

    def __init__(self, index: int, track: Track, liked: bool = False):
        super().__init__()
        self.index = index
        self.track = track
        self._liked = liked

        h = QHBoxLayout(self)
        h.setContentsMargins(6, 4, 6, 4)

        self.cover = QLabel()
        self.cover.setFixedSize(self.COVER_SIZE, self.COVER_SIZE)
        self.cover.setStyleSheet("background:#2a2a2a;")

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedWidth(32)
        self.play_btn.clicked.connect(lambda: self.play_clicked.emit(self.index))

        title = QLabel(f"<b>{track.title or '—'}</b>  <span style='color:#888'>— {_artists_str(track)}</span>")
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setMinimumWidth(200)

        dur = QLabel(_fmt_duration(track.duration_ms))
        dur.setStyleSheet("color:#888")
        dur.setFixedWidth(50)

        self.like_btn = QPushButton()
        self.like_btn.setFixedWidth(32)
        self._update_like_icon()
        self.like_btn.clicked.connect(self._on_like)

        h.addWidget(self.cover)
        h.addWidget(self.play_btn)
        h.addWidget(title, 1)
        h.addWidget(dur)
        h.addWidget(self.like_btn)

        uri = cover_uri_for(track)
        if uri:
            run(download_cover, uri, "50x50",
                on_result=self._set_cover, pool=cover_pool())

    def _set_cover(self, path: Optional[str]) -> None:
        if not path:
            return
        pix = QPixmap(path)
        if pix.isNull():
            return
        self.cover.setPixmap(
            pix.scaled(
                self.COVER_SIZE, self.COVER_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _update_like_icon(self) -> None:
        self.like_btn.setText("♥" if self._liked else "♡")

    def _on_like(self) -> None:
        self._liked = not self._liked
        self._update_like_icon()
        tid = self.track.track_id or self.track.id
        self.like_toggled.emit(tid, self._liked)


class TrackList(QListWidget):
    """Generic list of tracks with play/like buttons."""
    play_requested = pyqtSignal(int)  # index

    def __init__(self, api: Api):
        super().__init__()
        self.api = api
        self._tracks: List[Track] = []
        self._liked_ids: set = set()

    def set_liked_ids(self, ids: set) -> None:
        self._liked_ids = ids

    def set_tracks(self, tracks: List[Track]) -> None:
        self.clear()
        self._tracks = []
        self.append_tracks(list(tracks))

    def append_tracks(self, tracks: List[Track]) -> None:
        start = len(self._tracks)
        for offset, t in enumerate(tracks):
            i = start + offset
            tid = str(t.track_id or t.id)
            row = TrackRow(i, t, liked=tid in self._liked_ids)
            row.play_clicked.connect(self.play_requested.emit)
            row.like_toggled.connect(self._handle_like)
            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, row)
            self._tracks.append(t)

    def tracks(self) -> List[Track]:
        return self._tracks

    def _handle_like(self, track_id, new_state: bool) -> None:
        from ..workers import run
        def op():
            if new_state:
                self.api.like(track_id)
            else:
                self.api.unlike(track_id)
        run(op)
        tid = str(track_id)
        if new_state:
            self._liked_ids.add(tid)
        else:
            self._liked_ids.discard(tid)


class SimpleList(QListWidget):
    """List of albums / artists / playlists with click callback."""
    item_activated = pyqtSignal(object)

    # Yandex avatars only serves a fixed set of sizes, so pick one of them.
    _SUPPORTED = (30, 50, 75, 80, 100, 200, 300, 400)

    def __init__(self, fmt: Callable[[object], str], icon_size: int = 50):
        super().__init__()
        self._fmt = fmt
        self._items: List[object] = []
        self._icon_size = icon_size
        # fetch size = smallest supported >= icon_size (fallback: largest)
        self._fetch_size = next(
            (s for s in self._SUPPORTED if s >= icon_size), self._SUPPORTED[-1]
        )
        self.setIconSize(QSize(icon_size, icon_size))
        self.itemDoubleClicked.connect(self._on_double)

    def set_items(self, items: List[object]) -> None:
        self.clear()
        self._items = []
        self.append_items(list(items))

    def append_items(self, items: List[object]) -> None:
        size_str = f"{self._fetch_size}x{self._fetch_size}"
        for obj in items:
            item = QListWidgetItem(self._fmt(obj))
            self.addItem(item)
            self._items.append(obj)
            uri = cover_uri_for(obj)
            if uri:
                idx = len(self._items) - 1
                run(
                    download_cover, uri, size_str,
                    on_result=self._make_icon_setter(idx),
                    pool=cover_pool(),
                )

    def _make_icon_setter(self, idx: int):
        def set_icon(path: Optional[str]) -> None:
            if not path or idx >= self.count():
                return
            pix = QPixmap(path)
            if not pix.isNull():
                self.item(idx).setIcon(QIcon(pix))
        return set_icon

    def items(self) -> List[object]:
        return self._items

    def _on_double(self, item: QListWidgetItem) -> None:
        idx = self.row(item)
        if 0 <= idx < len(self._items):
            self.item_activated.emit(self._items[idx])


def fmt_album(a: Album) -> str:
    artists = ", ".join(x.name for x in (a.artists or []) if x and x.name)
    return f"{a.title} — {artists}" if artists else a.title


def fmt_artist(a: Artist) -> str:
    return a.name or "—"


def fmt_playlist(p) -> str:
    return f"{p.title}  ({p.track_count})"

"""VLC-backed player with a simple queue and Qt signals."""
from __future__ import annotations

from typing import List, Optional

import vlc
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from yandex_music import Track

from .api import Api


class Player(QObject):
    track_changed = pyqtSignal(object)  # Track | None
    state_changed = pyqtSignal(bool)  # playing?
    position_changed = pyqtSignal(int, int)  # pos_ms, dur_ms

    def __init__(self, api: Api):
        super().__init__()
        self.api = api
        self._vlc = vlc.Instance("--no-video")
        self._mp = self._vlc.media_player_new()
        self._queue: List[Track] = []
        self._index: int = -1
        self._current: Optional[Track] = None

        self._tick = QTimer(self)
        self._tick.setInterval(500)
        self._tick.timeout.connect(self._emit_position)
        self._tick.start()

        events = self._mp.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end)

    # ---- queue -----------------------------------------------------------
    def set_queue(self, tracks: List[Track], start: int = 0) -> None:
        self._queue = list(tracks)
        self._index = start
        self._play_current()

    def play_track(self, track: Track) -> None:
        self.set_queue([track], 0)

    def next(self) -> None:
        if self._index + 1 < len(self._queue):
            self._index += 1
            self._play_current()

    def prev(self) -> None:
        if self._index > 0:
            self._index -= 1
            self._play_current()

    # ---- transport -------------------------------------------------------
    def toggle(self) -> None:
        if not self._current:
            return
        if self._mp.is_playing():
            self._mp.pause()
            self.state_changed.emit(False)
        else:
            self._mp.play()
            self.state_changed.emit(True)

    def pause(self) -> None:
        self._mp.pause()
        self.state_changed.emit(False)

    def stop(self) -> None:
        self._mp.stop()
        self.state_changed.emit(False)

    def seek(self, position_ms: int) -> None:
        length = self._mp.get_length()
        if length <= 0:
            return
        self._mp.set_time(max(0, min(position_ms, length)))

    def set_volume(self, volume_0_100: int) -> None:
        self._mp.audio_set_volume(int(volume_0_100))

    def volume(self) -> int:
        return int(self._mp.audio_get_volume())

    # ---- state ----------------------------------------------------------
    @property
    def current(self) -> Optional[Track]:
        return self._current

    def is_playing(self) -> bool:
        return bool(self._mp.is_playing())

    # ---- internals -------------------------------------------------------
    def _play_current(self) -> None:
        if not (0 <= self._index < len(self._queue)):
            self._current = None
            self.track_changed.emit(None)
            return
        track = self._queue[self._index]
        try:
            url = self.api.stream_url(track)
        except Exception:
            url = None
        if not url:
            # skip on failure
            self._index += 1
            if self._index < len(self._queue):
                self._play_current()
            return
        media = self._vlc.media_new(url)
        self._mp.set_media(media)
        self._mp.play()
        self._current = track
        self.track_changed.emit(track)
        self.state_changed.emit(True)

    def _on_end(self, _event) -> None:
        # called from a VLC thread; schedule on Qt thread
        QTimer.singleShot(0, self.next)

    def _emit_position(self) -> None:
        length = self._mp.get_length()
        pos = self._mp.get_time()
        if length < 0:
            length = 0
        if pos < 0:
            pos = 0
        self.position_changed.emit(pos, length)

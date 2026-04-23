from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)
from yandex_music import Track

from ..player import Player


def _artists_str(track: Track) -> str:
    return ", ".join(a.name for a in (track.artists or []) if a and a.name) or "—"


def _fmt_time(ms: int) -> str:
    if ms <= 0:
        return "0:00"
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


class PlayerBar(QWidget):
    def __init__(self, player: Player):
        super().__init__()
        self.player = player
        self._user_dragging = False

        self.title = QLabel("—")
        self.title.setTextFormat(Qt.TextFormat.RichText)

        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.next_btn = QPushButton("⏭")
        for b in (self.prev_btn, self.play_btn, self.next_btn):
            b.setFixedWidth(40)
        self.prev_btn.clicked.connect(player.prev)
        self.next_btn.clicked.connect(player.next)
        self.play_btn.clicked.connect(player.toggle)

        self.pos_slider = QSlider(Qt.Orientation.Horizontal)
        self.pos_slider.setRange(0, 0)
        self.pos_slider.sliderPressed.connect(lambda: setattr(self, "_user_dragging", True))
        self.pos_slider.sliderReleased.connect(self._on_seek_release)

        self.pos_label = QLabel("0:00 / 0:00")

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(player.volume())
        self.vol_slider.setFixedWidth(120)
        self.vol_slider.valueChanged.connect(player.set_volume)

        top = QHBoxLayout()
        top.addWidget(self.prev_btn)
        top.addWidget(self.play_btn)
        top.addWidget(self.next_btn)
        top.addWidget(self.title, 1)
        top.addWidget(QLabel("🔊"))
        top.addWidget(self.vol_slider)

        mid = QHBoxLayout()
        mid.addWidget(self.pos_slider, 1)
        mid.addWidget(self.pos_label)

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 4, 8, 4)
        v.addLayout(top)
        v.addLayout(mid)

        player.track_changed.connect(self._on_track)
        player.state_changed.connect(self._on_state)
        player.position_changed.connect(self._on_position)

    def _on_track(self, track: Optional[Track]) -> None:
        if not track:
            self.title.setText("—")
            return
        self.title.setText(
            f"<b>{_artists_str(track)}</b>  "
            f"<span style='color:#888'>— {track.title or '—'}</span>"
        )

    def _on_state(self, playing: bool) -> None:
        self.play_btn.setText("⏸" if playing else "▶")

    def _on_position(self, pos_ms: int, dur_ms: int) -> None:
        if self._user_dragging:
            return
        self.pos_slider.setRange(0, max(0, int(dur_ms)))
        self.pos_slider.setValue(int(pos_ms))
        self.pos_label.setText(f"{_fmt_time(pos_ms)} / {_fmt_time(dur_ms)}")

    def _on_seek_release(self) -> None:
        self.player.seek(int(self.pos_slider.value()))
        self._user_dragging = False

from __future__ import annotations

from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QVBoxLayout, QWidget,
)

from .. import settings, themes


class SettingsDialog(QDialog):
    """Modal settings window. Theme changes preview live; Cancel reverts."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.resize(420, 180)

        self._qapp = QApplication.instance()

        self._initial_theme = settings.get("theme") or "system"

        self.theme_combo = QComboBox()
        for tid, name in themes.THEMES:
            self.theme_combo.addItem(name, tid)
        idx = self.theme_combo.findData(self._initial_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        hint = QLabel(
            "Тема «macOS» подобрана под оформление последних версий macOS "
            "и рекомендуется для максимально приятного вида."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888;")

        form = QFormLayout()
        form.addRow("Тема оформления:", self.theme_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self._on_reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(hint)
        root.addStretch(1)
        root.addWidget(buttons)

    def _on_theme_changed(self) -> None:
        tid = self.theme_combo.currentData()
        if tid and self._qapp is not None:
            themes.apply_theme(self._qapp, tid)

    def _on_accept(self) -> None:
        tid = self.theme_combo.currentData() or "system"
        settings.set_value("theme", tid)
        self.accept()

    def _on_reject(self) -> None:
        if self._qapp is not None:
            themes.apply_theme(self._qapp, self._initial_theme)
        self.reject()

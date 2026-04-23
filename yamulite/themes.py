"""UI themes. Each theme is a QSS stylesheet applied to the QApplication."""
from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from . import settings

# "Системная" — no stylesheet, native Qt/platform look (current behavior).
SYSTEM_QSS = ""

# "macOS" — polished dark theme tuned to look at home on recent macOS releases.
# Uses the system accent blue and SF-style typography with translucent-feeling
# surfaces, rounded corners, and subtle hover states.
MACOS_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1f22;
    color: #ececec;
}

QLabel {
    background: transparent;
    color: #ececec;
}

QStatusBar {
    background: #18191b;
    color: #9a9a9a;
    border-top: 1px solid #2a2b2e;
}

QStatusBar::item {
    border: none;
}

/* Sidebar + list views */
QListWidget {
    background-color: #232428;
    border: 1px solid #2d2e32;
    border-radius: 10px;
    padding: 6px;
    outline: 0;
}
QListWidget::item {
    border-radius: 7px;
    padding: 6px 10px;
    margin: 1px 0;
    color: #dcdcdc;
}
QListWidget::item:hover {
    background-color: #2d2f34;
}
QListWidget::item:selected {
    background-color: #0A84FF;
    color: #ffffff;
}
QListWidget::item:selected:!active {
    background-color: #3a5470;
    color: #ffffff;
}

/* Text fields */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2a2b2f;
    border: 1px solid #3a3b40;
    border-radius: 7px;
    padding: 6px 10px;
    color: #ececec;
    selection-background-color: #0A84FF;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #0A84FF;
}
QLineEdit:disabled {
    color: #707070;
    background-color: #26272a;
}

/* Buttons */
QPushButton {
    background-color: #3a3b40;
    color: #f2f2f2;
    border: 1px solid #45464b;
    border-radius: 7px;
    padding: 5px 14px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #46474c;
}
QPushButton:pressed {
    background-color: #0A84FF;
    border-color: #0A84FF;
    color: #ffffff;
}
QPushButton:disabled {
    color: #6f6f6f;
    background-color: #2c2d30;
    border-color: #34353a;
}
QPushButton:default {
    background-color: #0A84FF;
    border-color: #0A84FF;
    color: #ffffff;
}
QPushButton:default:hover {
    background-color: #1f93ff;
}

/* Tabs */
QTabWidget::pane {
    background: #1e1f22;
    border: none;
    border-top: 1px solid #2d2e32;
    top: -1px;
}
QTabBar {
    qproperty-drawBase: 0;
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #a6a6a6;
    padding: 6px 14px;
    margin: 3px 3px 0 3px;
    border: 1px solid transparent;
    border-radius: 7px;
}
QTabBar::tab:hover {
    background: #2a2b2f;
    color: #dddddd;
}
QTabBar::tab:selected {
    background: #3a3b40;
    color: #ffffff;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #4a4b50;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #5a5b60;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #4a4b50;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #5a5b60;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    width: 0;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 4px;
    background: #3a3b40;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #0A84FF;
    border-radius: 2px;
}
QSlider::add-page:horizontal {
    background: #3a3b40;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
    border: 1px solid rgba(0, 0, 0, 0.25);
}
QSlider::handle:horizontal:hover {
    background: #f0f0f0;
}

/* Menus */
QMenuBar {
    background: #1e1f22;
    color: #ececec;
    border-bottom: 1px solid #2a2b2e;
}
QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 5px;
}
QMenuBar::item:selected {
    background: #2d2f34;
}
QMenu {
    background: #2a2b2f;
    color: #ececec;
    border: 1px solid #3a3b40;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 5px 18px;
    border-radius: 5px;
}
QMenu::item:selected {
    background: #0A84FF;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #3a3b40;
    margin: 4px 6px;
}

/* Combobox */
QComboBox {
    background-color: #2a2b2f;
    border: 1px solid #3a3b40;
    border-radius: 7px;
    padding: 5px 10px;
    color: #ececec;
    min-height: 22px;
}
QComboBox:hover {
    border-color: #4a4b50;
}
QComboBox:focus {
    border: 1px solid #0A84FF;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #2a2b2f;
    color: #ececec;
    border: 1px solid #3a3b40;
    border-radius: 7px;
    selection-background-color: #0A84FF;
    selection-color: #ffffff;
    outline: 0;
}

/* Tooltips */
QToolTip {
    background: #2a2b2f;
    color: #ececec;
    border: 1px solid #3a3b40;
    border-radius: 6px;
    padding: 4px 6px;
}
"""


# Ordered list for UI dropdowns. Each entry: (id, display name).
THEMES: list[tuple[str, str]] = [
    ("system", "Системная"),
    ("macos", "macOS"),
]

_QSS_BY_ID = {
    "system": SYSTEM_QSS,
    "macos": MACOS_QSS,
}


def theme_name(theme_id: str) -> str:
    for tid, name in THEMES:
        if tid == theme_id:
            return name
    return theme_id


_default_font: QFont | None = None


def _apply_font(app: QApplication, theme_id: str) -> None:
    """Use the platform's system UI font for both themes (SF on macOS,
    Segoe on Windows, etc.), which avoids Qt's missing-font warnings."""
    global _default_font
    if _default_font is None:
        _default_font = QFont(app.font())
    if theme_id == "macos":
        sys_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
        app.setFont(sys_font)
    else:
        app.setFont(_default_font)


def apply_theme(app: QApplication, theme_id: str) -> None:
    qss = _QSS_BY_ID.get(theme_id, SYSTEM_QSS)
    app.setStyleSheet(qss)
    _apply_font(app, theme_id)


def apply_saved_theme(app: QApplication) -> None:
    apply_theme(app, settings.get("theme") or "system")

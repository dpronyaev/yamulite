from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QCursor, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTabWidget, QVBoxLayout, QWidget,
)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(ev)

from ..auth import DeviceCode, request_device_code, save_token, wait_for_token


class _DeviceWorker(QThread):
    got_token = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, device: DeviceCode):
        super().__init__()
        self.device = device
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            token = wait_for_token(self.device, stop_flag=lambda: self._stop)
        except Exception as e:
            self.failed.emit(str(e))
            return
        self.got_token.emit(token)


class LoginWindow(QWidget):
    logged_in = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YAMULITE — вход")
        self.resize(480, 320)

        self._worker: _DeviceWorker | None = None

        tabs = QTabWidget(self)
        tabs.addTab(self._build_device_tab(), "Через браузер")
        tabs.addTab(self._build_token_tab(), "Ввести токен")

        root = QVBoxLayout(self)
        root.addWidget(tabs)

    # --- device tab -------------------------------------------------------
    def _build_device_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)

        self.status = QLabel("Нажмите «Получить код», чтобы начать вход.")
        self.status.setWordWrap(True)

        self.code_label = ClickableLabel("")
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_label.setStyleSheet("font-size: 32px; font-weight: bold; letter-spacing: 4px;")
        self.code_label.setToolTip("Нажмите, чтобы скопировать код")
        self.code_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.code_label.clicked.connect(self._copy_code)

        self.copy_hint = QLabel("")
        self.copy_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copy_hint.setStyleSheet("color: #4caf50;")

        self.url_btn = QPushButton("Открыть страницу подтверждения")
        self.url_btn.setEnabled(False)
        self.url_btn.clicked.connect(self._open_url)

        self.start_btn = QPushButton("Получить код")
        self.start_btn.clicked.connect(self._start_device_flow)

        v.addWidget(self.status)
        v.addWidget(self.code_label)
        v.addWidget(self.copy_hint)
        v.addWidget(self.url_btn)
        v.addWidget(self.start_btn)
        v.addStretch(1)
        return w

    def _start_device_flow(self) -> None:
        self.start_btn.setEnabled(False)
        self.status.setText("Запрашиваю код у Яндекса…")
        try:
            device = request_device_code()
        except Exception as e:
            self.start_btn.setEnabled(True)
            self.status.setText(f"Ошибка: {e}")
            return
        self._device = device
        self.code_label.setText(device.user_code)
        self.url_btn.setEnabled(True)
        self.status.setText(
            f"1. Откройте {device.verification_url}\n"
            f"2. Войдите в свой аккаунт Яндекса.\n"
            f"3. Введите код выше. Ожидаю подтверждения…"
        )
        self._worker = _DeviceWorker(device)
        self._worker.got_token.connect(self._on_token)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _open_url(self) -> None:
        if hasattr(self, "_device"):
            QDesktopServices.openUrl(QUrl(self._device.verification_url))

    def _copy_code(self) -> None:
        code = self.code_label.text().strip()
        if not code:
            return
        QApplication.clipboard().setText(code)
        self.copy_hint.setText("Код скопирован")
        QTimer.singleShot(1500, lambda: self.copy_hint.setText(""))

    def _on_token(self, token: str) -> None:
        save_token(token)
        self.logged_in.emit(token)

    def _on_failed(self, msg: str) -> None:
        self.status.setText(f"Ошибка: {msg}")
        self.start_btn.setEnabled(True)

    # --- manual token tab ------------------------------------------------
    def _build_token_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Вставьте готовый OAuth-токен Yandex Music:"))
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        v.addWidget(self.token_edit)

        row = QHBoxLayout()
        ok = QPushButton("Войти")
        ok.clicked.connect(self._submit_token)
        row.addStretch(1)
        row.addWidget(ok)
        v.addLayout(row)
        v.addStretch(1)
        return w

    def _submit_token(self) -> None:
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "YAMULITE", "Токен пуст.")
            return
        save_token(token)
        self.logged_in.emit(token)

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(1000)
        super().closeEvent(event)

import sys

from PyQt6.QtWidgets import QApplication

from .auth import load_token
from .themes import apply_saved_theme
from .ui.login import LoginWindow
from .ui.main_window import MainWindow

APP_NAME = "YAMULITE"


def _fix_macos_app_name(name: str) -> None:
    """Override the CFBundleName so the macOS menu bar shows the app's name
    instead of "Python" when running unbundled. Must run before QApplication."""
    if sys.platform != "darwin":
        return
    try:
        from Foundation import NSBundle  # type: ignore[import-not-found]
    except Exception:
        return
    bundle = NSBundle.mainBundle()
    if not bundle:
        return
    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    if info is not None:
        info["CFBundleName"] = name
        info["CFBundleDisplayName"] = name


def main() -> int:
    _fix_macos_app_name(APP_NAME)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    apply_saved_theme(app)

    token = load_token()
    if token:
        window = MainWindow(token)
        window.show()
    else:
        login = LoginWindow()

        def on_success(new_token: str) -> None:
            login.close()
            w = MainWindow(new_token)
            w.show()
            # keep reference alive
            app.setProperty("main_window", w)

        login.logged_in.connect(on_success)
        login.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

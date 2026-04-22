import sys

from PyQt6.QtWidgets import QApplication

from .auth import load_token
from .ui.login import LoginWindow
from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("YAMULITE")

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

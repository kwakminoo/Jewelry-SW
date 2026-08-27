"""Native PyQt6 launcher for Jewelry SW."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from jewelry.ui.window.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Jewelry SW")
    app.setStyle("Fusion")
    qss = Path(__file__).parent / "ui" / "resources" / "styles" / "theme.qss"
    app.setStyleSheet(qss.read_text(encoding="utf-8"))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

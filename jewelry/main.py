"""Native PyQt6 launcher for Jewelry SW."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from jewelry.ui.window.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Jewelry SW")
    app.setStyle("Fusion")
    icons_dir = (Path(__file__).parent / "ui" / "resources" / "icons").resolve().as_posix()
    qss = Path(__file__).parent / "ui" / "resources" / "styles" / "theme.qss"
    app.setStyleSheet(qss.read_text(encoding="utf-8").replace("{ICONS_DIR}", icons_dir))
    window = MainWindow()
    window.show()
    window.maximize_workspace()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

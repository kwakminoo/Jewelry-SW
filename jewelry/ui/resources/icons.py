"""Stable paths for bundled monochrome SVG icons."""

from pathlib import Path

from PyQt6.QtGui import QIcon

_ICON_DIR = Path(__file__).resolve().parent / "icons"


def app_icon(name: str) -> QIcon:
    return QIcon(str(_ICON_DIR / f"{name}.svg"))

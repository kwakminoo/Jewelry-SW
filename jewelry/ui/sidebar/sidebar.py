from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget


def _icon_pixmap(name: str, color: str) -> QPixmap:
    """Draw a crisp 18px navigation icon without text glyphs or image files."""
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name == "home":
        roof = QPainterPath(QPointF(4.5, 11))
        roof.lineTo(12, 4.5)
        roof.lineTo(19.5, 11)
        painter.drawPath(roof)
        painter.drawPath(QPainterPath(QPointF(6.5, 9.5)))
        painter.drawLine(QPointF(6.5, 9.5), QPointF(6.5, 19))
        painter.drawLine(QPointF(17.5, 9.5), QPointF(17.5, 19))
        painter.drawLine(QPointF(6.5, 19), QPointF(17.5, 19))
        painter.drawRect(QRectF(10, 14, 4, 5))
    elif name == "ledger":
        painter.drawRect(QRectF(5, 5, 14, 14))
        painter.drawLine(QPointF(5, 9), QPointF(19, 9))
        painter.drawLine(QPointF(10, 9), QPointF(10, 19))
    elif name == "report":
        painter.drawLine(QPointF(5, 19), QPointF(5, 13))
        painter.drawLine(QPointF(10, 19), QPointF(10, 8))
        painter.drawLine(QPointF(15, 19), QPointF(15, 11))
        painter.drawLine(QPointF(20, 19), QPointF(20, 5))
    elif name == "settings":
        painter.drawEllipse(QRectF(9, 9, 6, 6))
        for start, end in (
            ((12, 3.5), (12, 6.5)), ((12, 17.5), (12, 20.5)),
            ((3.5, 12), (6.5, 12)), ((17.5, 12), (20.5, 12)),
            ((5.9, 5.9), (8, 8)), ((16, 16), (18.1, 18.1)),
            ((18.1, 5.9), (16, 8)), ((8, 16), (5.9, 18.1)),
        ):
            painter.drawLine(QPointF(*start), QPointF(*end))
    elif name == "user":
        painter.drawEllipse(QRectF(9, 5, 6, 6))
        painter.drawArc(QRectF(5.5, 12, 13, 9), 0, 180 * 16)

    painter.end()
    return pixmap


def navigation_icon(name: str) -> QIcon:
    icon = QIcon()
    icon.addPixmap(_icon_pixmap(name, "#8a8a86"), QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(_icon_pixmap(name, "#ffffff"), QIcon.Mode.Normal, QIcon.State.On)
    icon.addPixmap(_icon_pixmap(name, "#0a0a0a"), QIcon.Mode.Active, QIcon.State.Off)
    return icon


class SidebarButton(QPushButton):
    def __init__(self, icon_name: str, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(38, 38)
        self.setIcon(navigation_icon(icon_name))
        self.setIconSize(QSize(18, 18))
        self.setToolTip(label)
        self.setText("")


class Sidebar(QWidget):
    page_selected = pyqtSignal(str)

    PAGES = [
        ("home", "home", "메인"),
        ("ledger", "ledger", "대장"),
        ("report", "report", "통계"),
        ("settings", "settings", "설정"),
    ]
    PAGE_TARGETS = {
        "home": "main",
        "ledger": "main",
        "report": "main",
        "settings": "settings",
    }
    WIDTH = 52

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(self.WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 10, 7, 10)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._buttons: dict[str, SidebarButton] = {}
        for key, icon_name, label in self.PAGES:
            button = SidebarButton(icon_name, label, self)
            button.clicked.connect(lambda _checked=False, k=key: self._select(k))
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
            self._buttons[key] = button

        layout.addStretch(1)
        user = QPushButton(self)
        user.setObjectName("sidebarUserButton")
        user.setFixedSize(38, 38)
        user.setIcon(navigation_icon("user"))
        user.setIconSize(QSize(18, 18))
        user.setToolTip("사용자")
        layout.addWidget(user, 0, Qt.AlignmentFlag.AlignHCenter)

        self._select("home")

    def _select(self, key: str) -> None:
        for page_key, button in self._buttons.items():
            button.setChecked(page_key == key)
        self.page_selected.emit(self.PAGE_TARGETS[key])

from PyQt6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizeGrip, QStackedWidget, QVBoxLayout, QWidget

from jewelry.config.settings import APP_NAME
from jewelry.ui.pages.equipment_page import EquipmentPage
from jewelry.ui.pages.ledger_page import MainPage
from jewelry.ui.pages.settings_page import SettingsPage
from jewelry.ui.sidebar.sidebar import Sidebar
from jewelry.ui.resources.icons import app_icon


class WindowControlButton(QPushButton):
    def __init__(self, control: str, parent=None) -> None:
        super().__init__(parent)
        self.control = control
        self.setObjectName(f"{control}Button")
        self.setFixedSize(39, 34)
        self.setIconSize(QSize(12, 12))
        self.setIcon(app_icon(f"window-{control}"))


class TitleBar(QFrame):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._drag_origin: QPoint | None = None
        self.setObjectName("titleBar")
        self.setFixedHeight(35)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 0, 0, 0)
        row.setSpacing(0)
        mark = QLabel(self); mark.setObjectName("brandMark"); mark.setFixedSize(11, 11); row.addWidget(mark)
        row.addSpacing(7)
        brand = QLabel("JEWELRY SW", self); brand.setObjectName("brandName"); row.addWidget(brand)
        row.addSpacing(7)
        divider = QLabel("/", self); divider.setObjectName("titleMuted"); row.addWidget(divider)
        row.addSpacing(7)
        subtitle = QLabel("입출고 대장", self); subtitle.setObjectName("titleMuted"); row.addWidget(subtitle)
        row.addStretch(1)
        for control, callback in (("minimize", window.showMinimized), ("maximize", self._toggle_maximized), ("close", window.close)):
            button = WindowControlButton(control, self)
            button.clicked.connect(callback); row.addWidget(button)
            if control == "maximize": self.maximize_button = button

    def _toggle_maximized(self) -> None:
        self._window.toggle_workspace_maximized()
        QTimer.singleShot(0, self.update_maximize_icon)

    def update_maximize_icon(self) -> None:
        state = "restore" if self._window.is_workspace_maximized() else "maximize"
        name = f"window-{state}"
        self.maximize_button.setIcon(app_icon(name))
        self.maximize_button.setProperty("windowStateIcon", state)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton: self._toggle_maximized()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            if self._window.is_workspace_maximized():
                return
            self._drag_origin = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(1440, 930)
        self.setMinimumSize(1120, 720)
        self._normal_minimum_size = QSize(1120, 720)
        self._workspace_maximized = False
        self._normal_geometry = QRect()
        central = QWidget(self); central.setObjectName("windowShell"); self.setCentralWidget(central)
        shell = QVBoxLayout(central); shell.setContentsMargins(1, 1, 1, 1); shell.setSpacing(0)
        self.title_bar = TitleBar(self)
        shell.addWidget(self.title_bar)
        body = QWidget(self); layout = QHBoxLayout(body); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0); shell.addWidget(body, 1)
        self.sidebar = Sidebar(self); layout.addWidget(self.sidebar)
        self.pages = QStackedWidget(self); layout.addWidget(self.pages, 1)
        self.size_grip = QSizeGrip(self)
        self.size_grip.setObjectName("windowSizeGrip")
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.raise_()
        self._page_index = {}
        self._register_page("main", MainPage(self)); self._register_page("equipment", EquipmentPage(self)); self._register_page("settings", SettingsPage(self))
        self.sidebar.page_selected.connect(self._show_page)

    def _register_page(self, key: str, widget: QWidget) -> None:
        self._page_index[key] = self.pages.addWidget(widget)

    def _show_page(self, key: str) -> None:
        self.pages.setCurrentIndex(self._page_index[key])

    def is_workspace_maximized(self) -> bool:
        return self._workspace_maximized or self.isMaximized()

    def toggle_workspace_maximized(self) -> None:
        """Maximize to the usable desktop, never underneath the taskbar."""
        if self.is_workspace_maximized():
            if self.isMaximized():
                self.showNormal()
            self._workspace_maximized = False
            self.setMinimumSize(self._normal_minimum_size)
            if self._normal_geometry.isValid():
                self.setGeometry(self._normal_geometry)
        else:
            self._normal_geometry = QRect(self.geometry())
            screen = self.screen()
            if screen is not None:
                available = screen.availableGeometry()
                self.setMinimumSize(
                    min(self._normal_minimum_size.width(), available.width()),
                    min(self._normal_minimum_size.height(), available.height()),
                )
                self._workspace_maximized = True
                self.setGeometry(available)
        self.size_grip.setVisible(not self._workspace_maximized and not self.isMaximized())
        self.title_bar.update_maximize_icon()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.size_grip.move(self.width() - self.size_grip.width(), self.height() - self.size_grip.height())
        self.size_grip.raise_()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "title_bar"):
            QTimer.singleShot(0, self.title_bar.update_maximize_icon)

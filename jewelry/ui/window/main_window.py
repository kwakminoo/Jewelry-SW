import ctypes
import sys
from ctypes import wintypes

from PyQt6.QtCore import QAbstractNativeEventFilter, QEvent, QPoint, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizeGrip, QStackedWidget, QVBoxLayout, QWidget

from jewelry.config.settings import APP_NAME
from jewelry.ui.pages.ledger_history_page import LedgerHistoryPage
from jewelry.ui.pages.ledger_page import MainPage
from jewelry.ui.pages.settings_page import SettingsPage
from jewelry.ui.pages.statistics_page import StatisticsPage
from jewelry.ui.sidebar.sidebar import Sidebar
from jewelry.ui.resources.icons import app_icon

_IS_WINDOWS = sys.platform == "win32"

WM_NCCALCSIZE = 0x0083
WM_NCHITTEST = 0x0084
RESIZE_BORDER = 7

HTLEFT, HTRIGHT, HTTOP, HTBOTTOM = 10, 11, 12, 15
HTTOPLEFT, HTTOPRIGHT, HTBOTTOMLEFT, HTBOTTOMRIGHT = 13, 14, 16, 17


if _IS_WINDOWS:
    class _MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("message", wintypes.UINT),
            ("wParam", wintypes.WPARAM),
            ("lParam", wintypes.LPARAM),
            ("time", wintypes.DWORD),
            ("pt", wintypes.POINT),
        ]


class _FramelessNativeFilter(QAbstractNativeEventFilter):
    """Handles WM_NCCALCSIZE / WM_NCHITTEST for `window` via QApplication's
    native event filter instead of overriding QWidget.nativeEvent(), which
    crashes with an illegal instruction on this PyQt6 build.

    There is no WM_GETMINMAXINFO handling here anymore: maximize is done
    manually in MainWindow via setGeometry(screen.availableGeometry()), so
    there's no native showMaximized() call left for Windows to compute
    bounds for."""

    def __init__(self, window: "MainWindow") -> None:
        super().__init__()
        self._window = window

    def nativeEventFilter(self, eventType, message):
        # An unhandled Python exception escaping this callback (called from C++)
        # crashes the process outright on this PyQt6 build, so every path below
        # must be defensive: guard the NULL-hwnd case explicitly and keep a
        # blanket try/except as a last-resort safety net.
        if not _IS_WINDOWS or bytes(eventType) not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0
        try:
            msg = _MSG.from_address(int(message))
            # NOTE: this deliberately compares against the *cached*
            # self._window._hwnd rather than re-reading self._window.winId()
            # here. Calling winId() from inside a native event callback was
            # tried and reproducibly crashes this PyQt6 build (illegal
            # instruction) - it is not reentrancy-safe on this build. The
            # cache is safe because a top-level window's native handle never
            # changes after creation.
            if msg.hwnd is None or int(msg.hwnd) != self._window._hwnd:
                return False, 0
            if msg.message == WM_NCCALCSIZE:
                # Windows keeps WS_THICKFRAME on a FramelessWindowHint window
                # (that's what makes native edge-drag resizing possible), and
                # WS_THICKFRAME reserves an invisible resize border around the
                # client area by default. That border isn't applied the same
                # way once the window fills availableGeometry() via our manual
                # maximize, so the visible content size shifts by a few px
                # between normal and "maximized" states. Handling this message
                # ourselves and returning 0 without adjusting the proposed
                # rect makes the client rect equal the window rect - no
                # border, so the size never shifts.
                return True, 0
            if msg.message == WM_NCHITTEST and not self._window.is_workspace_maximized():
                hit = self._window._hit_test(msg.lParam)
                if hit is not None:
                    return True, hit
        except Exception:
            pass
        return False, 0


class WindowControlButton(QPushButton):
    def __init__(self, control: str, parent=None) -> None:
        super().__init__(parent)
        self.control = control
        self.setObjectName(f"{control}Button")
        self.setFixedSize(39, 34)
        self.setIconSize(QSize(12, 12))
        self.setIcon(app_icon(f"window-{control}"))


_DRAG_RESTORE_THRESHOLD = 4


class TitleBar(QFrame):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._drag_origin: QPoint | None = None
        self._press_origin: QPoint | None = None
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
            self._press_origin = event.globalPosition().toPoint()
            if self._window.is_workspace_maximized():
                self._drag_origin = None
            else:
                self._drag_origin = self._press_origin - self._window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        global_pos = event.globalPosition().toPoint()
        if self._window.is_workspace_maximized():
            if self._press_origin is None:
                return
            delta = global_pos - self._press_origin
            if delta.manhattanLength() < _DRAG_RESTORE_THRESHOLD:
                return
            # Restore using the geometry saved before maximizing (not
            # showNormal(), since maximize is our own geometry hack, not a
            # real Qt window state), keeping the cursor's relative x
            # position on the titlebar stable. ratio must be computed from
            # the press position RELATIVE to the window's own left edge, not
            # the raw global x - on a secondary monitor whose origin isn't
            # (0, 0), global x can exceed the window width and push ratio
            # past 1.0, throwing the restored window off to the side.
            window_left = self._window.frameGeometry().left()
            relative_x = self._press_origin.x() - window_left
            ratio = min(1.0, max(0.0, relative_x / max(self._window.width(), 1)))
            self._window.restore_workspace()
            target_x = global_pos.x() - int(self._window.width() * ratio)
            target_y = global_pos.y() - self.height() // 2
            self._window.move(target_x, target_y)
            self._drag_origin = global_pos - self._window.frameGeometry().topLeft()
            self._press_origin = None
            return
        if self._drag_origin is not None:
            self._window.move(global_pos - self._drag_origin)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None
        self._press_origin = None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(1440, 930)
        self.setMinimumSize(1120, 720)
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
        self._register_page("main", MainPage(self))
        self._register_page("ledger", LedgerHistoryPage(self)); self._register_page("report", StatisticsPage(self))
        self._register_page("settings", SettingsPage(self))
        self.sidebar.page_selected.connect(self._show_page)

        # Manual "workspace maximize": we size the window to the current
        # monitor's availableGeometry() ourselves (see maximize_workspace())
        # instead of calling showMaximized(), so maximized/normal state and
        # the geometry to restore to are tracked explicitly rather than via
        # isMaximized().
        self._workspace_maximized = False
        self._normal_geometry: QRect | None = None

        self._hwnd = int(self.winId())
        self._native_filter = _FramelessNativeFilter(self) if _IS_WINDOWS else None
        if self._native_filter is not None:
            QApplication.instance().installNativeEventFilter(self._native_filter)

    def _register_page(self, key: str, widget: QWidget) -> None:
        self._page_index[key] = self.pages.addWidget(widget)

    def _show_page(self, key: str) -> None:
        self.pages.setCurrentIndex(self._page_index[key])

    def is_workspace_maximized(self) -> bool:
        return self._workspace_maximized

    def maximize_workspace(self) -> None:
        if self._workspace_maximized:
            return
        screen = self.screen()
        if screen is None:
            return
        self._normal_geometry = self.geometry()
        self._workspace_maximized = True
        self.setGeometry(screen.availableGeometry())
        self.size_grip.hide()
        QTimer.singleShot(0, self.title_bar.update_maximize_icon)

    def restore_workspace(self) -> None:
        if not self._workspace_maximized:
            return
        self._workspace_maximized = False
        if self._normal_geometry is not None:
            self.setGeometry(self._normal_geometry)
        self.size_grip.show()
        QTimer.singleShot(0, self.title_bar.update_maximize_icon)

    def toggle_workspace_maximized(self) -> None:
        if self._workspace_maximized:
            self.restore_workspace()
        else:
            self.maximize_workspace()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if not self._workspace_maximized:
            self.size_grip.move(self.width() - self.size_grip.width(), self.height() - self.size_grip.height())
        self.size_grip.setVisible(not self._workspace_maximized)
        self.size_grip.raise_()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if hasattr(self, "title_bar"):
                QTimer.singleShot(0, self.title_bar.update_maximize_icon)
            if hasattr(self, "size_grip"):
                self.size_grip.setVisible(not self._workspace_maximized)

    def _hit_test(self, lparam: int) -> int | None:
        """WM_NCHITTEST: turn the outer RESIZE_BORDER px of the frameless window into
        native resize handles so the OS drives edge/corner resizing itself."""
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        ratio = self.devicePixelRatioF() or 1.0
        origin = self.frameGeometry().topLeft()
        local_x = int(x / ratio) - origin.x()
        local_y = int(y / ratio) - origin.y()
        w, h = self.width(), self.height()
        left, right = local_x <= RESIZE_BORDER, local_x >= w - RESIZE_BORDER
        top, bottom = local_y <= RESIZE_BORDER, local_y >= h - RESIZE_BORDER
        if top and left: return HTTOPLEFT
        if top and right: return HTTOPRIGHT
        if bottom and left: return HTBOTTOMLEFT
        if bottom and right: return HTBOTTOMRIGHT
        if left: return HTLEFT
        if right: return HTRIGHT
        if top: return HTTOP
        if bottom: return HTBOTTOM
        return None

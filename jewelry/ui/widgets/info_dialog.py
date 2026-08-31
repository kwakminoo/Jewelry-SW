"""엑셀 내보내기 완료 등 단순 안내에 쓰는, 앱과 같은 스타일의 알림 다이얼로그.

기본 QMessageBox는 OS 기본 스타일이라 프레임리스 검정/흰색 디자인과 어울리지
않는다. StartSessionDialog/EntryDetailDialog와 같은 appDialogShell 패턴을
재사용해 통일된 느낌을 준다.
"""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from jewelry.ui.resources.icons import app_icon


class InfoDialog(QDialog):
    def __init__(self, title: str, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appDialogShell")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(340)
        self._drag_origin: QPoint | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1); outer.setSpacing(0)
        outer.addWidget(self._build_title_bar(title))

        body = QWidget(self); body.setObjectName("appDialogBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 18, 20, 18); body_layout.setSpacing(18)

        message_label = QLabel(message, self)
        message_label.setObjectName("dialogMessage")
        message_label.setWordWrap(True)
        body_layout.addWidget(message_label)

        footer = QHBoxLayout(); footer.addStretch(1)
        confirm_btn = QPushButton("확인", self); confirm_btn.setObjectName("dialogPrimaryButton")
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self.accept)
        footer.addWidget(confirm_btn)
        body_layout.addLayout(footer)
        outer.addWidget(body)

    def _build_title_bar(self, title: str) -> QFrame:
        frame = QFrame(self); frame.setObjectName("appDialogTitleBar"); frame.setFixedHeight(48)
        row = QHBoxLayout(frame); row.setContentsMargins(20, 0, 8, 0); row.setSpacing(0)
        label = QLabel(title, frame); label.setObjectName("appDialogTitle")
        row.addWidget(label); row.addStretch(1)
        close_btn = QPushButton(frame); close_btn.setObjectName("appDialogClose")
        close_btn.setIcon(app_icon("window-close")); close_btn.clicked.connect(self.reject)
        row.addWidget(close_btn)
        return frame

    @classmethod
    def show_message(cls, parent: QWidget | None, title: str, message: str) -> None:
        cls(title, message, parent).exec()

    # ------------------------------------------------------------ 창 이동 (frameless)
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 48:
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from jewelry.ui.resources.icons import app_icon


class StartSessionDialog(QDialog):
    """시작 버튼을 누르면 뜨는 공정(광/연마) · 카라트(14K/18K) 선택 창."""

    CATEGORIES = ["광", "연마"]
    KARATS = ["14K", "18K"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appDialogShell")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(360)
        self._drag_origin: QPoint | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1); outer.setSpacing(0)
        outer.addWidget(self._build_title_bar())

        body = QWidget(self); body.setObjectName("appDialogBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 18, 20, 18); body_layout.setSpacing(14)

        field_row = QHBoxLayout(); field_row.setSpacing(14)
        self.category_combo = self._build_combo_field("공정", self.CATEGORIES, field_row)
        self.karat_combo = self._build_combo_field("카라트", self.KARATS, field_row)
        body_layout.addLayout(field_row)

        divider = QFrame(body); divider.setObjectName("appDialogDivider"); divider.setFrameShape(QFrame.Shape.HLine)
        body_layout.addWidget(divider)

        body_layout.addLayout(self._build_footer_row())
        outer.addWidget(body)

    def _build_title_bar(self) -> QFrame:
        frame = QFrame(self); frame.setObjectName("appDialogTitleBar"); frame.setFixedHeight(48)
        row = QHBoxLayout(frame); row.setContentsMargins(20, 0, 8, 0); row.setSpacing(0)
        title = QLabel("작업 시작", frame); title.setObjectName("appDialogTitle")
        row.addWidget(title); row.addStretch(1)
        close_btn = QPushButton(frame); close_btn.setObjectName("appDialogClose")
        close_btn.setIcon(app_icon("window-close")); close_btn.clicked.connect(self.reject)
        row.addWidget(close_btn)
        return frame

    def _build_combo_field(self, label_text: str, options: list[str], row: QHBoxLayout) -> QComboBox:
        col = QVBoxLayout(); col.setSpacing(6)
        label = QLabel(label_text, self); label.setObjectName("dialogFieldLabel")
        col.addWidget(label)
        combo = QComboBox(self); combo.setObjectName("dialogFieldCombo")
        combo.addItems(options)
        col.addWidget(combo)
        row.addLayout(col, 1)
        return combo

    def _build_footer_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(10); row.addStretch(1)
        cancel_btn = QPushButton("취소", self); cancel_btn.setObjectName("dialogCancelButton")
        cancel_btn.clicked.connect(self.reject)
        start_btn = QPushButton("시작", self); start_btn.setObjectName("dialogPrimaryButton")
        start_btn.clicked.connect(self.accept)
        row.addWidget(cancel_btn); row.addWidget(start_btn)
        return row

    def selection(self) -> tuple[str, str]:
        return self.category_combo.currentText(), self.karat_combo.currentText()

    @classmethod
    def get_selection(cls, parent: QWidget | None = None) -> tuple[str, str] | None:
        dialog = cls(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selection()
        return None

    # ------------------------------------------------------------ 창 이동 (frameless)
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 48:
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None

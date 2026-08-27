from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from jewelry.ui.resources.icons import app_icon


class PhotoThumbnail(QPushButton):
    """Uniform SVG photo button; centering is handled by the table cell wrapper."""

    THUMB_SIZE = 29

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("photoButton")
        self.setFixedSize(self.THUMB_SIZE, self.THUMB_SIZE)
        self.setIcon(app_icon("photo"))
        self.setIconSize(QSize(16, 16))
        self.setToolTip("사진 보기")
        self.clicked.connect(self._show_large)

    def _show_large(self) -> None:
        dialog = QDialog(self.window())
        dialog.setWindowTitle("사진 보기")
        dialog.setMinimumSize(360, 220)
        layout = QVBoxLayout(dialog)
        icon = QLabel(dialog)
        icon.setPixmap(app_icon("photo").pixmap(QSize(48, 48)))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(icon)
        caption = QLabel("카메라 연동 전 임시 이미지입니다.", dialog)
        caption.setObjectName("mutedText")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(caption)
        layout.addStretch(1)
        dialog.exec()

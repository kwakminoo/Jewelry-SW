"""플랫한 세그먼트 토글 버튼 그룹 (예: 전체/광/연마, 월별/분기별/연간)."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget


class SegmentedControl(QWidget):
    current_changed = pyqtSignal(str)

    def __init__(self, options: list[str], parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        for index, option in enumerate(options):
            button = QPushButton(option, self)
            button.setObjectName("segmentButton")
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.clicked.connect(lambda _checked=False, value=option: self.current_changed.emit(value))
            self._group.addButton(button)
            layout.addWidget(button)
            self._buttons[option] = button

    def current(self) -> str:
        for option, button in self._buttons.items():
            if button.isChecked():
                return option
        return ""

    def set_current(self, option: str) -> None:
        if option in self._buttons:
            self._buttons[option].setChecked(True)

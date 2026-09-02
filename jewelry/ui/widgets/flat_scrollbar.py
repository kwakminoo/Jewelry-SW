"""손잡이 길이를 일정 이상 늘어나지 않게 제한한 스크롤바.

QSS의 max-height/max-width는 QScrollBar::handle 크기 계산에 반영되지
않는 Qt의 알려진 제약이라, 기본 페인팅(화살표·트랙)은 그대로 두고
손잡이만 지운 뒤 스크롤 위치 비율에 맞춰 짧은 손잡이를 다시 그린다.
(중앙 정렬로 단순히 잘라내면 맨 위/맨 아래에서 트랙 끝에 붙지 않는다.)
paintEvent를 통째로 새로 그리면 화살표 표시를 켜는 Qt 내부 로직까지
같이 사라지므로, 화살표·트랙은 네이티브 페인팅을 그대로 재사용한다.
"""

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QScrollBar, QStyle, QStyleOptionSlider

_MAX_HANDLE = 50
_ERASE_COLOR = QColor("#ffffff")
_NORMAL_COLOR = QColor("#d2d2ce")
_HOVER_COLOR = QColor("#090909")


class FlatScrollBar(QScrollBar):
    def _capped_rect(self, opt: QStyleOptionSlider) -> QRect:
        groove = self.style().subControlRect(QStyle.ComplexControl.CC_ScrollBar, opt, QStyle.SubControl.SC_ScrollBarGroove, self)
        vertical = self.orientation() == Qt.Orientation.Vertical
        track_len = groove.height() if vertical else groove.width()
        length = min(_MAX_HANDLE, track_len)
        span = self.maximum() - self.minimum()
        movable = max(0, track_len - length)
        ratio = (self.value() - self.minimum()) / span if span else 0.0
        offset = round(movable * ratio)
        if vertical:
            return QRect(groove.left(), groove.top() + offset, groove.width(), length)
        return QRect(groove.left() + offset, groove.top(), length, groove.height())

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        native = self.style().subControlRect(QStyle.ComplexControl.CC_ScrollBar, opt, QStyle.SubControl.SC_ScrollBarSlider, self)
        vertical = self.orientation() == Qt.Orientation.Vertical
        native_length = native.height() if vertical else native.width()
        if native_length <= _MAX_HANDLE:
            return

        painter = QPainter(self)
        painter.fillRect(native, _ERASE_COLOR)
        hovered = bool(opt.activeSubControls & QStyle.SubControl.SC_ScrollBarSlider)
        painter.fillRect(self._capped_rect(opt), _HOVER_COLOR if hovered else _NORMAL_COLOR)

"""휠 스크롤에 브라우저(크롬 등)와 비슷한 느낌의 감속 애니메이션을 붙인다.

기본 Qt 휠 스크롤은 한 틱마다 스크롤바 값을 즉시(애니메이션 없이) 점프시켜
뚝뚝 끊기는 느낌을 준다. 여기서는 뷰포트의 휠 이벤트를 가로채 목표값까지
easing 곡선으로 이동시키고, 짧은 시간 안에 연속으로 휠이 들어오면 진행 중인
애니메이션의 목표값에 더해서 자연스럽게 이어지도록 한다.
"""

from PyQt6.QtCore import QEasingCurve, QEvent, QObject, QPointF, QPropertyAnimation
from PyQt6.QtWidgets import QAbstractScrollArea, QApplication

_DURATION_MS = 380


def _web_ease_curve() -> QEasingCurve:
    """CSS `scroll-behavior: smooth`가 쓰는 표준 `ease` 곡선
    (cubic-bezier(0.25, 0.1, 0.25, 1))과 동일하게 맞춘 커브."""
    curve = QEasingCurve(QEasingCurve.Type.BezierSpline)
    curve.addCubicBezierSegment(QPointF(0.25, 0.1), QPointF(0.25, 1.0), QPointF(1.0, 1.0))
    return curve


class _SmoothWheelFilter(QObject):
    def __init__(self, area: QAbstractScrollArea) -> None:
        super().__init__(area)
        self._area = area
        self._target: int | None = None
        self._animation = QPropertyAnimation(area.verticalScrollBar(), b"value", self)
        self._animation.setEasingCurve(_web_ease_curve())
        self._animation.setDuration(_DURATION_MS)
        self._animation.finished.connect(self._on_finished)

    def _on_finished(self) -> None:
        self._target = None

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() != QEvent.Type.Wheel:
            return False
        bar = self._area.verticalScrollBar()
        delta = event.angleDelta().y()
        if delta == 0 or bar.maximum() == bar.minimum():
            return False
        notches = delta / 120
        step = bar.singleStep() * QApplication.wheelScrollLines()
        base = self._target if self._target is not None else bar.value()
        target = max(bar.minimum(), min(bar.maximum(), base - int(notches * step)))
        self._target = target
        self._animation.stop()
        self._animation.setStartValue(bar.value())
        self._animation.setEndValue(target)
        self._animation.start()
        return True


def enable_smooth_scroll(area: QAbstractScrollArea) -> None:
    """area.viewport()의 휠 이벤트를 가로채 세로 스크롤을 부드럽게 애니메이션한다."""
    area.viewport().installEventFilter(_SmoothWheelFilter(area))

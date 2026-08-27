from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from jewelry.ui.resources.icons import app_icon


class StatCard(QFrame):
    """상단 대시보드에 쓰이는 카드 한 장 (제목 + 큰 값 + 보조 문구)."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setFixedHeight(94)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(24, 14, 18, 11)
        self._layout.setSpacing(2)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("statTitle")
        self._layout.addWidget(self.title_label)

        self.value_row = QHBoxLayout()
        self.value_row.setSpacing(6)
        self.value_label = QLabel(self)
        self.value_label.setObjectName("statValue")
        self.value_row.addWidget(self.value_label)
        self.value_row.addStretch(1)
        self._layout.addLayout(self.value_row)

        self.subtitle_label = QLabel(self)
        self.subtitle_label.setObjectName("statSubtitle")
        self._layout.addWidget(self.subtitle_label)

        self._layout.addStretch(1)

    def set_value(self, value_html: str) -> None:
        self.value_label.setText(value_html)

    def set_subtitle(self, text: str) -> None:
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))


class MonthNavCard(StatCard):
    """기준 월 카드. 값 오른쪽에 이전/다음 달 버튼이 붙는다."""

    def __init__(self, parent=None) -> None:
        super().__init__("기준 월", parent)
        self.value_label.setObjectName("monthNavValue")

        self.prev_btn = QToolButton(self)
        self.prev_btn.setObjectName("monthNavButton")
        self.prev_btn.setIcon(app_icon("chevron-left"))
        self.prev_btn.setIconSize(QSize(12, 12))

        self.next_btn = QToolButton(self)
        self.next_btn.setObjectName("monthNavButton")
        self.next_btn.setIcon(app_icon("chevron-right"))
        self.next_btn.setIconSize(QSize(12, 12))

        # AlignBottom alone drops the buttons flush against the row's bottom
        # edge, below the date text's visual baseline. A small bottom margin
        # on this wrapper raises them back up to line up with it.
        nav_wrap = QWidget(self)
        nav_layout = QVBoxLayout(nav_wrap)
        nav_layout.setContentsMargins(0, 0, 0, 6)
        nav_layout.setSpacing(0)
        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.next_btn)
        nav_layout.addLayout(nav_row)

        self.value_row.insertSpacing(1, 10)
        self.value_row.insertWidget(2, nav_wrap, 0, Qt.AlignmentFlag.AlignBottom)

        self.subtitle_label.setVisible(False)


class MiniTrendChart(QWidget):
    """최근 N개월 차익 추이를 보여주는 작은 막대 그래프."""

    def __init__(self, values: list[float], labels: tuple[str, str], parent=None) -> None:
        super().__init__(parent)
        self._values = values
        self._labels = labels
        self.setMinimumHeight(43)

    def set_values(self, values: list[float]) -> None:
        self._values = values
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if not self._values:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        bar_area_bottom = rect.height() - 14
        max_value = max(self._values) or 1.0

        count = len(self._values)
        gap = 3
        bar_width = max(2.0, (rect.width() - gap * (count - 1)) / count)

        for i, value in enumerate(self._values):
            height = max(3.0, (value / max_value) * (bar_area_bottom - 4))
            x = i * (bar_width + gap)
            y = bar_area_bottom - height
            is_last = i == count - 1
            color = QColor("#1f2430") if is_last else QColor("#e4e6ec")
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRect(int(x), int(y), int(bar_width), int(height))

        painter.setPen(QColor("#9aa0ab"))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(0, rect.height(), self._labels[0])
        left_label, right_label = self._labels
        metrics = painter.fontMetrics()
        painter.drawText(rect.width() - metrics.horizontalAdvance(right_label), rect.height(), right_label)

        painter.end()


class TrendCard(StatCard):
    """12개월 차익 추이 카드. 값 라벨 대신 미니 막대 그래프를 보여준다."""

    def __init__(self, title: str, values: list[float], labels: tuple[str, str], parent=None) -> None:
        super().__init__(title, parent)
        self.value_label.setVisible(False)
        self.subtitle_label.setVisible(False)

        self.chart = MiniTrendChart(values, labels, self)
        self._layout.addWidget(self.chart, 1)

    def set_values(self, values: list[float]) -> None:
        self.chart.set_values(values)

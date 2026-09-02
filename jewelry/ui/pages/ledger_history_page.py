"""기록 보기 화면: 월 선택 + 날짜별 작업 기록. 실제 데이터 연동 전 목업 값 사용."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from jewelry.ui.widgets.flat_scrollbar import FlatScrollBar
from jewelry.ui.widgets.segmented_control import SegmentedControl
from jewelry.ui.widgets.smooth_scroll import enable_smooth_scroll

MONTHS = [
    {"label": "2026.08", "count": 30, "yield_pct": 90.4, "diff": 43.90},
    {"label": "2026.07", "count": 34, "yield_pct": 88.7, "diff": 31.55},
    {"label": "2026.06", "count": 28, "yield_pct": 94.1, "diff": -6.20},
    {"label": "2026.05", "count": 41, "yield_pct": 86.2, "diff": 52.10},
    {"label": "2026.04", "count": 26, "yield_pct": 91.8, "diff": 18.35},
    {"label": "2026.03", "count": 33, "yield_pct": 89.5, "diff": 24.70},
    {"label": "2026.02", "count": 22, "yield_pct": 95.3, "diff": -2.85},
    {"label": "2026.01", "count": 29, "yield_pct": 87.9, "diff": 37.40},
]

RECORDS_BY_MONTH = {
    "2026.08": [
        {"date": "2026.08.26", "weekday": "수", "entries": [
            {"time": "14:22", "category": "광", "item": "반지", "in": 15.20, "out": 14.80},
            {"time": "13:05", "category": "광", "item": "목걸이", "in": 9.35, "out": 9.00},
            {"time": "11:40", "category": "연마", "item": "귀걸이", "in": 9.70, "out": 8.15},
        ]},
        {"date": "2026.08.25", "weekday": "화", "entries": [
            {"time": "17:41", "category": "광", "item": "귀걸이", "in": 22.10, "out": 21.55},
            {"time": "11:18", "category": "광", "item": "반지", "in": 8.75, "out": 8.40},
        ]},
        {"date": "2026.08.24", "weekday": "월", "entries": [
            {"time": "16:30", "category": "광", "item": "팔찌", "in": 18.40, "out": 17.20},
            {"time": "09:52", "category": "연마", "item": "팔찌", "in": 14.20, "out": 12.05},
        ]},
        {"date": "2026.08.22", "weekday": "토", "entries": [
            {"time": "15:07", "category": "광", "item": "반지", "in": 12.65, "out": 11.90},
            {"time": "10:20", "category": "연마", "item": "반지", "in": 8.85, "out": 7.40},
        ]},
        {"date": "2026.08.21", "weekday": "금", "entries": [
            {"time": "10:44", "category": "광", "item": "목걸이", "in": 14.05, "out": 13.55},
            {"time": "18:12", "category": "광", "item": "귀걸이", "in": 7.90, "out": 7.35},
        ]},
    ],
}

_FALLBACK_ITEMS = ["반지", "목걸이", "팔찌", "귀걸이"]
_FALLBACK_WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def _records_for(month_label: str) -> list[dict]:
    """월별 상세 기록. 8월 외에는 화면 확인용 축약 샘플만 제공한다."""
    if month_label in RECORDS_BY_MONTH:
        return RECORDS_BY_MONTH[month_label]
    seed = sum(ord(c) for c in month_label)
    return [
        {"date": f"{month_label}.{(seed % 20) + 1:02d}", "weekday": _FALLBACK_WEEKDAYS[seed % 7], "entries": [
            {"time": "14:00", "category": "광", "item": _FALLBACK_ITEMS[seed % 4], "in": 10.0 + (seed % 10), "out": 9.5 + (seed % 10)},
            {"time": "10:30", "category": "연마", "item": _FALLBACK_ITEMS[(seed + 1) % 4], "in": 6.0 + (seed % 6), "out": 5.6 + (seed % 6)},
        ]},
    ]


class MonthRow(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, month: dict, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("monthRow")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._label = month["label"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.label_widget = QLabel(month["label"], self)
        self.label_widget.setObjectName("monthRowLabel")
        top.addWidget(self.label_widget)
        top.addStretch(1)
        self.diff_widget = QLabel(f"{month['diff']:+.2f}", self)
        self.diff_widget.setObjectName("monthRowDiff")
        top.addWidget(self.diff_widget)
        layout.addLayout(top)

        self.meta_widget = QLabel(f"{month['count']}건 · 수율 {month['yield_pct']:.1f}%", self)
        self.meta_widget.setObjectName("monthRowMeta")
        layout.addWidget(self.meta_widget)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        for widget in (self, self.label_widget, self.diff_widget, self.meta_widget):
            widget.setProperty("selected", selected)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._label)
        super().mousePressEvent(event)


class MonthListPanel(QFrame):
    month_selected = pyqtSignal(str)

    def __init__(self, months: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("monthListPanel")
        self.setFixedWidth(240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        head = QFrame(self)
        head.setObjectName("monthListHead")
        head_row = QHBoxLayout(head)
        head_row.setContentsMargins(18, 14, 18, 14)
        title = QLabel("월 선택", head)
        title.setObjectName("mutedText")
        head_row.addWidget(title)
        head_row.addStretch(1)
        year = QLabel(months[0]["label"].split(".")[0] if months else "", head)
        year.setObjectName("mutedText")
        head_row.addWidget(year)
        layout.addWidget(head)

        scroll = QScrollArea(self)
        scroll.setObjectName("workScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBar(FlatScrollBar(Qt.Orientation.Vertical, scroll))
        enable_smooth_scroll(scroll)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        self._rows: dict[str, MonthRow] = {}
        for month in months:
            row = MonthRow(month, body)
            row.clicked.connect(self.month_selected.emit)
            body_layout.addWidget(row)
            self._rows[month["label"]] = row
        body_layout.addStretch(1)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

    def select(self, label: str) -> None:
        for key, row in self._rows.items():
            row.set_selected(key == label)


class ProcessBadge(QLabel):
    def __init__(self, category: str, parent=None) -> None:
        super().__init__(category, parent)
        self.setObjectName("processBadgeSolid" if category == "광" else "processBadgeOutline")
        self.setFixedSize(40, 21)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class DateGroup(QWidget):
    def __init__(self, group: dict, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame(self)
        header.setObjectName("dateGroupHeader")
        header.setFixedHeight(32)
        head_row = QHBoxLayout(header)
        head_row.setContentsMargins(18, 0, 18, 0)
        head_row.setSpacing(8)
        date_label = QLabel(group["date"], header)
        date_label.setObjectName("dateGroupTitle")
        head_row.addWidget(date_label)
        weekday_label = QLabel(group["weekday"], header)
        weekday_label.setObjectName("dateGroupWeekday")
        head_row.addWidget(weekday_label)
        head_row.addStretch(1)
        count_label = QLabel(f"{len(group['entries'])}건", header)
        count_label.setObjectName("dateGroupCount")
        head_row.addWidget(count_label)
        layout.addWidget(header)

        for entry in group["entries"]:
            layout.addWidget(self._record_row(entry))

    def _record_row(self, entry: dict) -> QFrame:
        row = QFrame(self)
        row.setObjectName("recordRow")
        row.setFixedHeight(44)
        row.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        h = QHBoxLayout(row)
        h.setContentsMargins(18, 0, 18, 0)
        h.setSpacing(14)

        time_label = QLabel(entry["time"], row)
        time_label.setObjectName("recordTime")
        time_label.setFixedWidth(44)
        h.addWidget(time_label)
        h.addWidget(ProcessBadge(entry["category"], row), 0, Qt.AlignmentFlag.AlignVCenter)
        item_label = QLabel(entry["item"], row)
        item_label.setObjectName("recordItem")
        item_label.setFixedWidth(70)
        h.addWidget(item_label)
        weight_label = QLabel(f"{entry['in']:.2f} → {entry['out']:.2f}", row)
        weight_label.setObjectName("recordWeight")
        h.addWidget(weight_label)
        h.addStretch(1)
        diff = entry["in"] - entry["out"]
        diff_label = QLabel(f"{diff:+.2f}", row)
        diff_label.setObjectName("recordDiff")
        h.addWidget(diff_label)
        return row


class LedgerHistoryPage(QWidget):
    """ledger 아이콘 대상 화면: 월별 작업 기록을 날짜별로 보여준다."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.month_panel = MonthListPanel(MONTHS, self)
        self.month_panel.month_selected.connect(self._select_month)
        outer.addWidget(self.month_panel)

        divider = QFrame(self)
        divider.setObjectName("verticalDivider")
        outer.addWidget(divider)

        right = QWidget(self)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(28, 22, 28, 0)
        right_layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.setSpacing(24)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        head_label = QLabel("선택한 달", right)
        head_label.setObjectName("mutedText")
        title_col.addWidget(head_label)
        self.month_title = QLabel(right)
        self.month_title.setObjectName("monthNavValue")
        title_col.addWidget(self.month_title)
        header_row.addLayout(title_col)
        header_row.addStretch(1)
        self.count_stat = self._inline_stat("기록", right, header_row)
        self.diff_stat = self._inline_stat("순 차익", right, header_row)
        self.yield_stat = self._inline_stat("수율", right, header_row)
        right_layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        filter_label = QLabel("공정", right)
        filter_label.setObjectName("mutedText")
        filter_row.addWidget(filter_label)
        self.process_filter = SegmentedControl(["전체", "광", "연마"], right)
        self.process_filter.current_changed.connect(self._apply_filter)
        filter_row.addWidget(self.process_filter)
        filter_row.addStretch(1)
        export_btn = QPushButton("엑셀 내보내기", right)
        export_btn.setObjectName("exportButton")
        filter_row.addWidget(export_btn)
        right_layout.addLayout(filter_row)

        scroll = QScrollArea(right)
        scroll.setObjectName("workScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBar(FlatScrollBar(Qt.Orientation.Vertical, scroll))
        enable_smooth_scroll(scroll)
        self.list_body = QWidget()
        self.list_layout = QVBoxLayout(self.list_body)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch(1)
        scroll.setWidget(self.list_body)
        right_layout.addWidget(scroll, 1)

        footer = QFrame(right)
        footer.setObjectName("gridFooter")
        footer.setFixedHeight(38)
        footer_row = QHBoxLayout(footer)
        footer_row.setContentsMargins(4, 0, 4, 0)
        self.sort_label = QLabel(footer)
        self.sort_label.setObjectName("footerText")
        footer_row.addWidget(self.sort_label)
        footer_row.addStretch(1)
        self.period_label = QLabel(footer)
        self.period_label.setObjectName("footerText")
        footer_row.addWidget(self.period_label)
        right_layout.addWidget(footer)

        outer.addWidget(right, 1)

        self._current_month = MONTHS[0]["label"] if MONTHS else ""
        self.month_panel.select(self._current_month)
        self._render_month(self._current_month)

    def _inline_stat(self, label_text: str, parent: QWidget, row: QHBoxLayout) -> QLabel:
        col = QVBoxLayout()
        col.setSpacing(2)
        label = QLabel(label_text, parent)
        label.setObjectName("inlineStatLabel")
        col.addWidget(label)
        value = QLabel(parent)
        value.setObjectName("inlineStatValue")
        col.addWidget(value)
        row.addLayout(col)
        return value

    def _select_month(self, label: str) -> None:
        self._current_month = label
        self.month_panel.select(label)
        self._render_month(label)

    def _apply_filter(self, _value: str) -> None:
        self._render_month(self._current_month)

    def _render_month(self, label: str) -> None:
        month = next((m for m in MONTHS if m["label"] == label), MONTHS[0] if MONTHS else None)
        if month is None:
            return
        self.month_title.setText(month["label"])
        self.count_stat.setText(f"{month['count']}건")
        self.diff_stat.setText(f"{month['diff']:+.2f} g")
        self.yield_stat.setText(f"{month['yield_pct']:.1f}%")

        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        process = self.process_filter.current()
        for group in _records_for(label):
            entries = group["entries"] if process == "전체" else [e for e in group["entries"] if e["category"] == process]
            if not entries:
                continue
            filtered_group = {**group, "entries": entries}
            self.list_layout.insertWidget(self.list_layout.count() - 1, DateGroup(filtered_group, self.list_body))

        self.sort_label.setText(f"최근 순 정렬 · {month['count']}건")
        self.period_label.setText(f"{label} 기준")

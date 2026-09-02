"""통계 화면: 월별 집계 테이블, 차익 추이 차트, 공정별 집계. 실제 데이터 연동 전 목업 값 사용."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from jewelry.ui.widgets.flat_scrollbar import FlatScrollBar
from jewelry.ui.widgets.segmented_control import SegmentedControl
from jewelry.ui.widgets.smooth_scroll import enable_smooth_scroll
from jewelry.ui.widgets.stat_card import StatCard

# 최신 순(2026.08 -> 2026.01). 표는 이 순서 그대로, 차익 추이 차트는 뒤집어 오래된 순으로 그린다.
MONTHLY_ROWS = [
    {"label": "2026.08", "k14_in": 208.75, "k14_out": 181.40, "k18_in": 246.10, "k18_out": 229.55, "yield_pct": 90.3},
    {"label": "2026.07", "k14_in": 195.30, "k14_out": 172.85, "k18_in": 231.60, "k18_out": 218.40, "yield_pct": 91.6},
    {"label": "2026.06", "k14_in": 182.45, "k14_out": 168.90, "k18_in": 214.75, "k18_out": 208.20, "yield_pct": 94.9},
    {"label": "2026.05", "k14_in": 224.60, "k14_out": 190.15, "k18_in": 258.30, "k18_out": 235.90, "yield_pct": 88.2},
    {"label": "2026.04", "k14_in": 176.20, "k14_out": 158.65, "k18_in": 202.45, "k18_out": 190.80, "yield_pct": 92.3},
    {"label": "2026.03", "k14_in": 199.85, "k14_out": 178.30, "k18_in": 226.15, "k18_out": 210.55, "yield_pct": 91.3},
    {"label": "2026.02", "k14_in": 154.90, "k14_out": 145.20, "k18_in": 181.35, "k18_out": 176.40, "yield_pct": 95.6},
    {"label": "2026.01", "k14_in": 211.40, "k14_out": 184.75, "k18_in": 238.90, "k18_out": 219.30, "yield_pct": 89.7},
]

PROCESS_SUMMARY = [
    {"name": "광", "in": 1128.40, "out": 1024.65, "yield_pct": 91.0},
    {"name": "연마", "in": 425.05, "out": 371.20, "yield_pct": 87.3},
]

# 기록 보기 화면의 8개월 합계(30+34+28+41+26+33+22+29)와 맞춘 값.
TOTAL_RECORDS = 243


def _month_diff(row: dict) -> float:
    return (row["k14_in"] - row["k14_out"]) + (row["k18_in"] - row["k18_out"])


def _totals() -> tuple[float, float, float]:
    in_total = sum(row["k14_in"] + row["k18_in"] for row in MONTHLY_ROWS)
    out_total = sum(row["k14_out"] + row["k18_out"] for row in MONTHLY_ROWS)
    return in_total, out_total, in_total - out_total


class MonthlyBarChart(QWidget):
    """월별 총 차익 추이. 가장 최근 달(맨 오른쪽)만 검정으로 강조한다."""

    def __init__(self, rows: list[dict], parent=None) -> None:
        super().__init__(parent)
        self._rows = rows
        self.setMinimumHeight(180)

    def paintEvent(self, event) -> None:  # noqa: N802
        if not self._rows:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        label_h = 18
        bar_area_bottom = rect.height() - label_h
        values = [_month_diff(row) for row in self._rows]
        max_value = max(values) or 1.0
        count = len(self._rows)
        gap = 10
        bar_width = max(4.0, (rect.width() - gap * (count - 1)) / count)

        for i, row in enumerate(self._rows):
            height = max(3.0, (values[i] / max_value) * (bar_area_bottom - 6))
            x = i * (bar_width + gap)
            y = bar_area_bottom - height
            is_last = i == count - 1
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0a0a0a") if is_last else QColor("#e4e6ec"))
            painter.drawRect(int(x), int(y), int(bar_width), int(height))

            painter.setPen(QColor("#9aa0ab"))
            label = row["label"].split(".")[-1]
            metrics = painter.fontMetrics()
            tx = int(x + bar_width / 2 - metrics.horizontalAdvance(label) / 2)
            painter.drawText(tx, rect.height() - 4, label)
        painter.end()


class YieldBar(QWidget):
    """수율을 나타내는 얇은 가로 진행 막대."""

    def __init__(self, percent: float, parent=None) -> None:
        super().__init__(parent)
        self._percent = max(0.0, min(100.0, percent))
        self.setFixedHeight(8)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ececea"))
        painter.drawRect(self.rect())
        fill_width = int(self.width() * self._percent / 100)
        painter.setBrush(QColor("#0a0a0a"))
        painter.drawRect(0, 0, fill_width, self.height())
        painter.end()


class ProcessSummaryPanel(QFrame):
    def __init__(self, rows: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("processSummaryPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        title = QLabel("공정별 집계", self)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for col, text in enumerate(["공정", "입고", "출고", "차익"]):
            label = QLabel(text, self)
            label.setObjectName("mutedText")
            grid.addWidget(label, 0, col)
        for r, row in enumerate(rows, start=1):
            grid.addWidget(QLabel(row["name"], self), r, 0)
            grid.addWidget(QLabel(f"{row['in']:.2f}", self), r, 1)
            grid.addWidget(QLabel(f"{row['out']:.2f}", self), r, 2)
            diff_label = QLabel(f"{row['in'] - row['out']:+.2f}", self)
            diff_label.setObjectName("recordDiff")
            grid.addWidget(diff_label, r, 3)
        layout.addLayout(grid)

        for row in rows:
            yield_row = QHBoxLayout()
            yield_row.setSpacing(10)
            name_label = QLabel(f"{row['name']} 수율", self)
            name_label.setObjectName("mutedText")
            name_label.setFixedWidth(70)
            yield_row.addWidget(name_label)
            yield_row.addWidget(YieldBar(row["yield_pct"], self), 1)
            pct_label = QLabel(f"{row['yield_pct']:.1f}%", self)
            pct_label.setObjectName("recordDiff")
            yield_row.addWidget(pct_label)
            layout.addLayout(yield_row)

        layout.addStretch(1)


class StatisticsPage(QWidget):
    """report 아이콘 대상 화면: 월별 집계 표 + 차익 추이 + 공정별 집계."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 24)
        outer.setSpacing(18)

        outer.addWidget(self._build_stat_row())

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        self.range_control = SegmentedControl(["월별", "분기별", "연간"], self)
        toolbar.addWidget(self.range_control)
        toolbar.addStretch(1)
        export_btn = QPushButton("엑셀 내보내기", self)
        export_btn.setObjectName("exportButton")
        toolbar.addWidget(export_btn)
        outer.addLayout(toolbar)

        outer.addWidget(self._build_table())

        bottom = QHBoxLayout()
        bottom.setSpacing(18)
        bottom.addWidget(self._build_chart_panel(), 3)
        bottom.addWidget(ProcessSummaryPanel(PROCESS_SUMMARY, self), 2)
        outer.addLayout(bottom, 1)

        footer = QHBoxLayout()
        left = QLabel(f"{len(MONTHLY_ROWS)}개월 집계 · {TOTAL_RECORDS}건", self)
        left.setObjectName("mutedText")
        footer.addWidget(left)
        footer.addStretch(1)
        right = QLabel("수율 = 출고 ÷ 입고", self)
        right.setObjectName("mutedText")
        footer.addWidget(right)
        outer.addLayout(footer)

    def _build_stat_row(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("statCardRow")
        row = QHBoxLayout(frame)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        period_card = StatCard("집계 기간", frame)
        period_card.set_value(f"2026 상반기~{MONTHLY_ROWS[0]['label'].split('.')[1]}")

        in_total, out_total, diff_total = _totals()
        unit = "<span style='font-size:14px;color:#9aa0ab;'>g</span>"
        in_card = StatCard("누적 입고", frame)
        in_card.set_value(f"{in_total:,.2f} {unit}")
        out_card = StatCard("누적 출고", frame)
        out_card.set_value(f"{out_total:,.2f} {unit}")
        diff_card = StatCard("누적 차익", frame)
        diff_unit = "<span style='font-size:14px;color:#cfcfc9;'>g</span>"
        diff_card.set_value(f"{diff_total:+,.2f} {diff_unit}")
        diff_card.set_highlighted(True)

        for card, stretch in ((period_card, 3), (in_card, 3), (out_card, 3), (diff_card, 4)):
            row.addWidget(card, stretch)
        return frame

    def _build_table(self) -> QTableWidget:
        table = QTableWidget(len(MONTHLY_ROWS) + 1, 8, self)
        table.setHorizontalHeaderLabels(["월", "14K 입고", "14K 출고", "14K 차익", "18K 입고", "18K 출고", "18K 차익", "수율"])
        table.verticalHeader().hide()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setVerticalScrollBar(FlatScrollBar(Qt.Orientation.Vertical, table))
        enable_smooth_scroll(table)

        for row, data in enumerate(MONTHLY_ROWS):
            k14_diff = data["k14_in"] - data["k14_out"]
            k18_diff = data["k18_in"] - data["k18_out"]
            values = [
                data["label"], f"{data['k14_in']:.2f}", f"{data['k14_out']:.2f}", f"{k14_diff:+.2f}",
                f"{data['k18_in']:.2f}", f"{data['k18_out']:.2f}", f"{k18_diff:+.2f}", f"{data['yield_pct']:.1f}%",
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                table.setItem(row, col, item)

        in_total, out_total, _diff_total = _totals()
        k14_in = sum(r["k14_in"] for r in MONTHLY_ROWS)
        k14_out = sum(r["k14_out"] for r in MONTHLY_ROWS)
        k18_in = sum(r["k18_in"] for r in MONTHLY_ROWS)
        k18_out = sum(r["k18_out"] for r in MONTHLY_ROWS)
        overall_yield = out_total / in_total * 100 if in_total else 0
        totals_row = [
            "합계", f"{k14_in:,.2f}", f"{k14_out:,.2f}", f"{k14_in - k14_out:+,.2f}",
            f"{k18_in:,.2f}", f"{k18_out:,.2f}", f"{k18_in - k18_out:+,.2f}", f"{overall_yield:.1f}%",
        ]
        last_row = len(MONTHLY_ROWS)
        for col, text in enumerate(totals_row):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(QBrush(QColor("#0a0a0a")))
            item.setForeground(QBrush(QColor("#ffffff")))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            table.setItem(last_row, col, item)
        return table

    def _build_chart_panel(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("processSummaryPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        title = QLabel("월별 총 차익 추이", frame)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        chart = MonthlyBarChart(list(reversed(MONTHLY_ROWS)), frame)
        layout.addWidget(chart, 1)
        return frame

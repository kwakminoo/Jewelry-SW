import csv

from PyQt6.QtCore import QDate, QSize, QTime, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from jewelry.ui.widgets.entry_grid import EntryGrid, FixedSummaryBar, LedgerHeader
from jewelry.ui.resources.icons import app_icon
from jewelry.ui.widgets.start_session_dialog import StartSessionDialog
from jewelry.ui.widgets.stat_card import MonthNavCard, StatCard, TrendCard
from jewelry.ui.sidebar.sidebar import navigation_icon

# 실제 데이터 연동 전 화면 확인용 샘플 값. 키가 없으면 빈 칸으로 표시된다.
SAMPLE_DATA = {
    "광": [
        {"date": "2026-08-26", "time": "14:22", "checked": True,
         ("14K", "in"): 15.20, ("14K", "out"): 14.80, ("18K", "in"): 30.50, ("18K", "out"): 29.90},
        {"date": "2026-08-26", "time": "13:05",
         ("14K", "in"): 9.35, ("14K", "out"): 9.00, ("18K", "in"): 18.25, ("18K", "out"): 17.80},
        {"date": "2026-08-25", "time": "17:41",
         ("14K", "in"): 22.10, ("14K", "out"): 21.55, ("18K", "in"): 12.40, ("18K", "out"): 12.05},
        {"date": "2026-08-25", "time": "11:18", "checked": True,
         ("14K", "in"): 8.75, ("14K", "out"): 8.40, ("18K", "in"): 26.90, ("18K", "out"): 25.10},
        {"date": "2026-08-24", "time": "16:30",
         ("14K", "in"): 18.40, ("14K", "out"): 17.20, ("18K", "in"): 33.15, ("18K", "out"): 31.60},
        {"date": "2026-08-24", "time": "09:52",
         ("14K", "in"): 6.20, ("14K", "out"): 5.95, ("18K", "in"): 11.05, ("18K", "out"): 10.70},
        {"date": "2026-08-22", "time": "15:07",
         ("14K", "in"): 12.65, ("14K", "out"): 11.90, ("18K", "in"): 21.30, ("18K", "out"): 20.15},
        {"date": "2026-08-21", "time": "18:12",
         ("14K", "in"): 7.90, ("14K", "out"): 7.35, ("18K", "in"): 9.85, ("18K", "out"): 9.20},
        {"date": "2026-08-21", "time": "10:44",
         ("14K", "in"): 14.05, ("14K", "out"): 13.55, ("18K", "in"): 28.60, ("18K", "out"): 27.90},
        {"date": "2026-08-20", "time": "12:36",
         ("14K", "in"): 11.30, ("14K", "out"): 10.80, ("18K", "in"): 24.45, ("18K", "out"): 23.90},
        {"date": "2026-08-19", "time": "14:59",
         ("14K", "in"): 19.75, ("14K", "out"): 18.60, ("18K", "in"): 35.20, ("18K", "out"): 34.05},
        {"date": "2026-08-18", "time": "08:47",
         ("14K", "in"): 5.45, ("14K", "out"): 5.10, ("18K", "in"): 8.90, ("18K", "out"): 8.55},
        {"date": "2026-08-15", "time": "16:03",
         ("14K", "in"): 13.20, ("14K", "out"): 12.65, ("18K", "in"): 22.75, ("18K", "out"): 21.90},
        {"date": "2026-08-14", "time": "13:28",
         ("14K", "in"): 16.85, ("14K", "out"): 16.10, ("18K", "in"): 31.40, ("18K", "out"): 30.25},
        {"date": "2026-08-13", "time": "10:11",
         ("14K", "in"): 4.95, ("14K", "out"): 4.60, ("18K", "in"): 7.20, ("18K", "out"): 6.85},
        {"date": "2026-08-12", "time": "17:25",
         ("14K", "in"): 21.65, ("14K", "out"): 20.15, ("18K", "in"): 38.15, ("18K", "out"): 36.30},
    ],
    "연마": [
        {"date": "2026-08-25", "time": "18:02",
         ("14K", "in"): 11.00, ("14K", "out"): 10.60, ("18K", "in"): 24.30, ("18K", "out"): 23.95},
        {"date": "2026-08-22", "time": "09:40",
         ("14K", "in"): 6.75, ("14K", "out"): 6.50, ("18K", "in"): 9.10, ("18K", "out"): 8.90},
        {"date": "2026-08-18", "time": "15:12",
         ("14K", "in"): 13.40, ("14K", "out"): 12.85, ("18K", "in"): 16.20, ("18K", "out"): 15.65},
    ],
}

# 12개월 차익 추이 카드용 샘플 값 (제일 오른쪽이 이번 달).
TREND_SAMPLE = [18.4, 22.1, 15.6, 27.3, 24.8, 19.2, 30.1, 26.5, 21.9, 33.4, 28.7, 43.9]


class ProcessTabWidget(QTabWidget):
    """QTabWidget with uninterrupted strip borders above all tabs/actions."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._top_line = QFrame(self)
        self._top_line.setObjectName("tabStripLine")
        self._bottom_line = QFrame(self)
        self._bottom_line.setObjectName("tabStripLine")
        for line in (self._top_line, self._bottom_line):
            line.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        bottom = max(0, self.tabBar().height() - 1)
        self._top_line.setGeometry(0, 0, self.width(), 1)
        self._bottom_line.setGeometry(0, bottom, self.width(), 1)
        self._top_line.raise_()
        self._bottom_line.raise_()


class ProcessTab(QWidget):
    """광 / 연마 탭 하나. 검색·필터·내보내기·기록 액션바 + 입출고 대장 표."""

    totals_changed = pyqtSignal()
    record_clicked = pyqtSignal()

    def __init__(self, category: str, sample_rows: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(0)
        self.category = category
        self._sample_rows = sample_rows

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.action_bar = self._build_action_bar()

        self.grid = EntryGrid(sample_rows, self)
        self.grid.changed.connect(self.totals_changed)
        layout.addWidget(self.grid, 1)

        layout.addWidget(self._build_footer())

        self.totals_changed.connect(self._update_footer)
        self._update_footer()

    def _build_action_bar(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("actionBar")
        row = QHBoxLayout(frame)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.meta_label = QLabel(frame)
        self.meta_label.setObjectName("tabMeta")
        row.addWidget(self.meta_label)
        row.addStretch(1)

        search_box = QFrame(frame)
        search_box.setObjectName("searchBox")
        search_row = QHBoxLayout(search_box)
        search_row.setContentsMargins(10, 0, 10, 0)
        search_row.setSpacing(6)
        search_icon = QLabel(search_box)
        search_icon.setObjectName("searchIcon")
        search_icon.setFixedSize(14, 14)
        search_icon.setPixmap(app_icon("search").pixmap(QSize(14, 14)))
        search_row.addWidget(search_icon)
        self.search_input = QLineEdit(search_box)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("품목 검색")
        self.search_input.textChanged.connect(lambda text: self.grid.filter_rows(text))
        search_row.addWidget(self.search_input)
        row.addWidget(search_box)

        filter_btn = QPushButton("필터", frame)
        filter_btn.setObjectName("filterButton")
        filter_btn.clicked.connect(self._show_filter_menu)
        row.addWidget(filter_btn)

        export_btn = QPushButton("엑셀 내보내기", frame)
        export_btn.setObjectName("exportButton")
        export_btn.clicked.connect(self._export_to_csv)
        row.addWidget(export_btn)

        self.record_btn = QPushButton("+  기록하기", frame)
        self.record_btn.setObjectName("recordButton")
        self.record_btn.setCheckable(True)
        self.record_btn.setToolTip("단축키: N")
        self.record_btn.clicked.connect(self.record_clicked)
        row.addWidget(self.record_btn)

        QShortcut(QKeySequence("N"), self, activated=self.record_btn.click)

        return frame

    def _build_footer(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("gridFooter")
        frame.setFixedHeight(46)
        row = QHBoxLayout(frame)
        row.setContentsMargins(4, 0, 4, 0)

        user_icon = QLabel(frame)
        user_icon.setObjectName("footerIcon")
        user_icon.setFixedSize(14, 14)
        user_icon.setPixmap(navigation_icon("user").pixmap(QSize(14, 14)))
        row.addWidget(user_icon)

        self.selection_label = QLabel(frame)
        self.selection_label.setObjectName("footerText")
        row.addWidget(self.selection_label)

        row.addStretch(1)

        self.autosave_label = QLabel(frame)
        self.autosave_label.setObjectName("footerText")
        row.addWidget(self.autosave_label)

        return frame

    def _update_footer(self) -> None:
        self.selection_label.setText(
            f"선택 {self.grid.selected_count()}건 · 총 {self.grid.data_row_count()}건"
        )
        self.autosave_label.setText(f"자동 저장됨 {QTime.currentTime().toString('HH:mm')}")

    def _show_filter_menu(self) -> None:
        menu = QMenu(self)
        for label, needle in (("전체 기록", ""), ("선택된 기록", "__selected__"), ("오늘 기록", QDate.currentDate().toString("yyyy.MM.dd"))):
            action = menu.addAction(label)
            action.triggered.connect(lambda _checked=False, n=needle: self._apply_filter(n))
        menu.exec(self.mapToGlobal(self.rect().topRight()))

    def _apply_filter(self, needle: str) -> None:
        if needle == "__selected__":
            self.grid.show_selected_only()
        else:
            self.search_input.setText(needle)

    def _export_to_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "CSV 내보내기", f"jewelry-{self.category}.csv", "CSV 파일 (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow(["날짜", "시간", "14K 입고", "14K 출고", "14K 차익", "18K 입고", "18K 출고", "18K 차익"])
            writer.writerows(self.grid.export_rows())
        QMessageBox.information(self, "내보내기 완료", f"{self.grid.data_row_count()}개 기록을 저장했습니다.")

    def weight(self, karat: str, direction: str) -> float:
        return self.grid.total_weight(karat, direction)

    def meta_label_text(self) -> str:
        latest = self.grid.latest_entry_label()
        count = self.grid.data_row_count()
        if latest:
            parts = latest.split()
            date = parts[0][5:] if parts and len(parts[0]) >= 10 else parts[0]
            time = parts[-1] if parts else ""
            return f"{count}건 · 마지막 입력 {date} {time}"
        return f"{count}건"


class MainPage(QWidget):
    """상단 요약 카드 + 광·연마 탭(검색·필터·표)으로 이루어진 메인 작업 화면."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._month = QDate.currentDate()
        self._active_session: tuple[str, str] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_stat_cards())

        self.tabs = ProcessTabWidget(self)
        self.tabs.setMinimumHeight(0)

        self.process_tabs = {
            "광": ProcessTab("광", SAMPLE_DATA["광"]),
            "연마": ProcessTab("연마", SAMPLE_DATA["연마"]),
        }
        for name, tab in self.process_tabs.items():
            self.tabs.addTab(tab, name)
            tab.totals_changed.connect(self._on_data_changed)
            tab.record_clicked.connect(self._on_record_clicked)
        first_tab = next(iter(self.process_tabs.values()))
        self.tabs.setCornerWidget(first_tab.action_bar, Qt.Corner.TopRightCorner)
        layout.addWidget(self.tabs, 1)

        self.tabs.currentChanged.connect(self._on_tab_changed)

        self._refresh_month_label()
        self._on_data_changed()

    # ------------------------------------------------------------ 상단 카드
    def _build_stat_cards(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("statCardRow")
        row = QHBoxLayout(frame)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self.month_card = MonthNavCard(frame)
        self.month_card.prev_btn.clicked.connect(lambda: self._shift_month(-1))
        self.month_card.next_btn.clicked.connect(lambda: self._shift_month(1))
        row.addWidget(self.month_card, 1)

        self.in_card = StatCard("총 입고", frame)
        self.in_card.set_subtitle("전월 대비 +12.4")  # TODO: 전월 데이터 연동 전 샘플 값
        row.addWidget(self.in_card, 1)

        self.out_card = StatCard("총 출고", frame)
        self.out_card.set_subtitle("전월 대비 +8.1")  # TODO: 전월 데이터 연동 전 샘플 값
        row.addWidget(self.out_card, 1)

        self.diff_card = StatCard("순 차익", frame)
        row.addWidget(self.diff_card, 1)

        self.trend_card = TrendCard("12개월 차익 추이", TREND_SAMPLE, ("26.09", "26.08"), frame)
        row.addWidget(self.trend_card, 2)

        return frame

    def _shift_month(self, delta: int) -> None:
        self._month = self._month.addMonths(delta)
        self._refresh_month_label()

    def _refresh_month_label(self) -> None:
        self.month_card.set_value(f"{self._month.year()}.{self._month.month():02d}")
        for tab in self.process_tabs.values():
            tab.grid.set_period_label(f"{self._month.year()}년 {self._month.month()}월")

    # -------------------------------------------------------------- 세션
    def _on_record_clicked(self) -> None:
        tab = self.tabs.currentWidget()
        if tab is None:
            return
        button = tab.record_btn
        if button.isChecked():
            selection = StartSessionDialog.get_selection(self)
            if selection is None:
                button.setChecked(False)
                return
            self._activate_session(*selection)
        else:
            self._deactivate_session()

    def _activate_session(self, category: str, karat: str) -> None:
        self._active_session = (category, karat)
        tab = self.process_tabs[category]
        self.tabs.setCurrentWidget(tab)
        for name, t in self.process_tabs.items():
            active_karat = karat if name == category else None
            t.grid.set_active(active_karat)
            t.record_btn.setChecked(name == category)
            t.record_btn.setText(f"중지 ({category} · {karat})" if name == category else "+  기록하기")

    def _deactivate_session(self) -> None:
        self._active_session = None
        for t in self.process_tabs.values():
            t.grid.set_active(None)
            t.record_btn.setChecked(False)
            t.record_btn.setText("+  기록하기")

    # -------------------------------------------------------------- 요약
    def _on_tab_changed(self, index: int) -> None:
        current = self.tabs.widget(index)
        if current is not None:
            self.tabs.setCornerWidget(current.action_bar, Qt.Corner.TopRightCorner)
        self._on_data_changed()

    def _on_data_changed(self) -> None:
        current = self.tabs.currentWidget()
        if current is None:
            return

        current.meta_label.setText(current.meta_label_text())

        total_in = current.weight("14K", "in") + current.weight("18K", "in")
        total_out = current.weight("14K", "out") + current.weight("18K", "out")
        diff = total_in - total_out
        yield_pct = (total_out / total_in * 100) if total_in else 0.0

        self.in_card.set_value(f"{total_in:.2f} <span style='font-size:14px;color:#9aa0ab;'>g</span>")
        self.out_card.set_value(f"{total_out:.2f} <span style='font-size:14px;color:#9aa0ab;'>g</span>")
        self.diff_card.set_value(f"{diff:+.2f} <span style='font-size:14px;color:#9aa0ab;'>g</span>")
        self.diff_card.set_subtitle(f"수율 {yield_pct:.1f}%")

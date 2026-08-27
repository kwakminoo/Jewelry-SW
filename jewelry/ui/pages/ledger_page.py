"""Stable main ledger layout: fixed header/total/footer and one shared action bar."""

import csv

from PyQt6.QtCore import QDate, QSize, QTime, Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox,
    QPushButton, QSizePolicy, QStackedWidget, QTabBar, QVBoxLayout, QWidget,
)

from jewelry.ui.pages.main_page import SAMPLE_DATA, TREND_SAMPLE
from jewelry.ui.resources.icons import app_icon
from jewelry.ui.sidebar.sidebar import navigation_icon
from jewelry.ui.widgets.entry_grid import EntryGrid, FixedSummaryBar, LedgerHeader
from jewelry.ui.widgets.start_session_dialog import StartSessionDialog
from jewelry.ui.widgets.stat_card import MonthNavCard, StatCard, TrendCard

TAB_ACTION_HEIGHT = 45


class TabActionRow(QFrame):
    """Full-height tab/action strip with non-layout-consuming edge lines."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent); self.setObjectName("tabActionRow"); self.setFixedHeight(TAB_ACTION_HEIGHT)
        self._top_line = QFrame(self); self._bottom_line = QFrame(self)
        for line in (self._top_line, self._bottom_line):
            line.setObjectName("tabActionLine"); line.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._top_line.setGeometry(0, 0, self.width(), 1)
        self._bottom_line.setGeometry(0, self.height() - 1, self.width(), 1)
        self._top_line.raise_(); self._bottom_line.raise_()


class ProcessTab(QWidget):
    def __init__(self, category: str, rows: list[dict], parent=None) -> None:
        super().__init__(parent); self.category = category; self.setMinimumHeight(0)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        self.header = LedgerHeader(self); self.grid = EntryGrid(rows, self); self.total_bar = FixedSummaryBar(self.grid, self)
        self.footer = self._footer()
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.total_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.footer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.header, 0); layout.addWidget(self.grid, 1); layout.addWidget(self.total_bar, 0); layout.addWidget(self.footer, 0)
        layout.setStretch(0, 0); layout.setStretch(1, 1); layout.setStretch(2, 0); layout.setStretch(3, 0)
        self.header.itemChanged.connect(self._header_changed)
        self.grid.changed.connect(self._changed)
        self.grid.horizontalHeader().sectionResized.connect(self._schedule_sync)
        QTimer.singleShot(0, self._sync_columns)
        self._changed()

    def _footer(self) -> QFrame:
        frame = QFrame(self); frame.setObjectName("gridFooter"); frame.setFixedHeight(46)
        row = QHBoxLayout(frame); row.setContentsMargins(12, 0, 14, 0); row.setSpacing(7)
        icon = QLabel(frame); icon.setObjectName("footerIcon"); icon.setFixedSize(14, 14)
        icon.setPixmap(navigation_icon("user").pixmap(QSize(14, 14))); row.addWidget(icon)
        self.selection_label = QLabel(frame); self.selection_label.setObjectName("footerText"); row.addWidget(self.selection_label)
        row.addStretch(1)
        self.autosave_label = QLabel(frame); self.autosave_label.setObjectName("footerText"); row.addWidget(self.autosave_label)
        return frame

    def _header_changed(self, item) -> None:
        if item.row() == 0 and item.column() == 0: self.grid.select_all(item.checkState())

    def _changed(self) -> None:
        self.total_bar.refresh()
        self.selection_label.setText(f"선택 {self.grid.selected_count()}건 · 총 {self.grid.data_row_count()}건")
        self.autosave_label.setText(f"자동 저장됨 {QTime.currentTime().toString('HH:mm')}")

    def _sync_columns(self, *_args) -> None:
        for col in range(self.grid.columnCount()):
            width = self.grid.columnWidth(col)
            self.header.setColumnWidth(col, width); self.total_bar.setColumnWidth(col, width)

    def _schedule_sync(self, *_args) -> None:
        QTimer.singleShot(0, self._sync_columns)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._schedule_sync()

    def set_period_label(self, label: str) -> None: self.total_bar.set_period_label(label)
    def weight(self, karat: str, direction: str) -> float: return self.grid.total_weight(karat, direction)
    def meta_label_text(self) -> str:
        latest = self.grid.latest_entry_label(); count = self.grid.data_row_count()
        if not latest: return f"{count}건"
        parts = latest.split(); date = parts[0][5:] if len(parts[0]) >= 10 else parts[0]
        return f"{count}건 · 마지막 입력 {date} {parts[-1]}"


class MainPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent); self._month = QDate.currentDate(); self._active_session = None
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        layout.addWidget(self._build_stat_cards())
        self.process_tabs = {name: ProcessTab(name, SAMPLE_DATA[name], self) for name in ("광", "연마")}
        for tab in self.process_tabs.values(): tab.grid.changed.connect(self._on_data_changed)
        self.tab_stack = QStackedWidget(self); self.tab_stack.setMinimumHeight(0)
        for tab in self.process_tabs.values(): self.tab_stack.addWidget(tab)
        self.tabs = self.tab_stack  # compatibility for callers/tests that need currentWidget().
        layout.addWidget(self._build_tab_action_row())
        layout.addWidget(self.tab_stack, 1)
        self._refresh_month_label(); self._on_tab_changed(0)

    def _build_stat_cards(self) -> QFrame:
        frame = QFrame(self); frame.setObjectName("statCardRow"); row = QHBoxLayout(frame)
        row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)
        self.month_card = MonthNavCard(frame); self.month_card.prev_btn.clicked.connect(lambda: self._shift_month(-1)); self.month_card.next_btn.clicked.connect(lambda: self._shift_month(1)); row.addWidget(self.month_card, 1)
        self.in_card = StatCard("총 입고", frame); self.in_card.set_subtitle("전월 대비 +12.4"); row.addWidget(self.in_card, 1)
        self.out_card = StatCard("총 출고", frame); self.out_card.set_subtitle("전월 대비 +8.1"); row.addWidget(self.out_card, 1)
        self.diff_card = StatCard("순 차익", frame); row.addWidget(self.diff_card, 1)
        self.trend_card = TrendCard("12개월 차익 추이", TREND_SAMPLE, ("26.09", "26.08"), frame); row.addWidget(self.trend_card, 2)
        return frame

    def _build_tab_action_row(self) -> QFrame:
        frame = TabActionRow(self)
        row = QHBoxLayout(frame); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)
        self.tab_bar = QTabBar(frame); self.tab_bar.setDrawBase(False); self.tab_bar.setDocumentMode(True); self.tab_bar.setUsesScrollButtons(False)
        for name in self.process_tabs: self.tab_bar.addTab(name)
        self.tab_bar.currentChanged.connect(self._on_tab_changed); row.addWidget(self.tab_bar)
        self.meta_label = QLabel(frame); self.meta_label.setObjectName("tabMeta"); row.addWidget(self.meta_label); row.addStretch(1)
        search = QFrame(frame); search.setObjectName("searchBox"); search_row = QHBoxLayout(search)
        search_row.setContentsMargins(10, 0, 10, 0); search_row.setSpacing(6); search_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel(search); icon.setObjectName("searchIcon"); icon.setFixedSize(14, 14); icon.setPixmap(app_icon("search").pixmap(QSize(14, 14))); search_row.addWidget(icon)
        self.search_input = QLineEdit(search); self.search_input.setObjectName("searchInput"); self.search_input.setPlaceholderText("품목 검색"); self.search_input.textChanged.connect(self._filter_current); search_row.addWidget(self.search_input); row.addWidget(search)
        self.filter_button = QPushButton("필터", frame); self.filter_button.setObjectName("filterButton"); self.filter_button.clicked.connect(self._show_filter_menu); row.addWidget(self.filter_button)
        self.export_button = QPushButton("엑셀 내보내기", frame); self.export_button.setObjectName("exportButton"); self.export_button.clicked.connect(self._export_current); row.addWidget(self.export_button)
        self.record_btn = QPushButton("+  기록하기", frame); self.record_btn.setObjectName("recordButton"); self.record_btn.setCheckable(True); self.record_btn.clicked.connect(self._on_record_clicked); row.addWidget(self.record_btn)
        QShortcut(QKeySequence("N"), self, activated=self.record_btn.click)
        return frame

    def _current_tab(self) -> ProcessTab: return self.tab_stack.currentWidget()
    def _on_tab_changed(self, index: int) -> None:
        if not hasattr(self, "tab_stack"): return
        self.tab_stack.setCurrentIndex(index)
        if hasattr(self, "search_input"):
            self.search_input.blockSignals(True); self.search_input.clear(); self.search_input.blockSignals(False)
            self._current_tab().grid.filter_rows("")
        self._on_data_changed()

    def _filter_current(self, text: str) -> None: self._current_tab().grid.filter_rows(text)
    def _show_filter_menu(self) -> None:
        menu = QMenu(self)
        for label, mode in (("전체 기록", ""), ("선택된 기록", "selected"), ("오늘 기록", QDate.currentDate().toString("yyyy.MM.dd"))):
            action = menu.addAction(label); action.triggered.connect(lambda _checked=False, value=mode: self._apply_filter(value))
        menu.exec(self.filter_button.mapToGlobal(self.filter_button.rect().bottomLeft()))

    def _apply_filter(self, value: str) -> None:
        if value == "selected": self._current_tab().grid.show_selected_only()
        else: self.search_input.setText(value)

    def _export_current(self) -> None:
        tab = self._current_tab(); path, _ = QFileDialog.getSaveFileName(self, "CSV 내보내기", f"jewelry-{tab.category}.csv", "CSV 파일 (*.csv)")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream); writer.writerow(["날짜", "시간", "14K 입고", "14K 출고", "14K 차익", "18K 입고", "18K 출고", "18K 차익"]); writer.writerows(tab.grid.export_rows())
        QMessageBox.information(self, "내보내기 완료", f"{tab.grid.data_row_count()}개 기록을 저장했습니다.")

    def _shift_month(self, delta: int) -> None: self._month = self._month.addMonths(delta); self._refresh_month_label()
    def _refresh_month_label(self) -> None:
        self.month_card.set_value(f"{self._month.year()}.{self._month.month():02d}")
        for tab in self.process_tabs.values(): tab.set_period_label(f"{self._month.year()}년 {self._month.month()}월")

    def _on_record_clicked(self) -> None:
        if self.record_btn.isChecked():
            selection = StartSessionDialog.get_selection(self)
            if selection is None: self.record_btn.setChecked(False); return
            self._activate_session(*selection)
        else: self._deactivate_session()

    def _activate_session(self, category: str, karat: str) -> None:
        self._active_session = (category, karat); index = list(self.process_tabs).index(category); self.tab_bar.setCurrentIndex(index)
        for name, tab in self.process_tabs.items(): tab.header.set_active(karat if name == category else None)
        self.record_btn.setChecked(True); self.record_btn.setText(f"중지 ({category} · {karat})")

    def _deactivate_session(self) -> None:
        self._active_session = None
        for tab in self.process_tabs.values(): tab.header.set_active(None)
        self.record_btn.setChecked(False); self.record_btn.setText("+  기록하기")

    def _on_data_changed(self) -> None:
        if not hasattr(self, "meta_label"): return
        current = self._current_tab(); self.meta_label.setText(current.meta_label_text())
        total_in = current.weight("14K", "in") + current.weight("18K", "in"); total_out = current.weight("14K", "out") + current.weight("18K", "out")
        diff = total_in - total_out; yield_pct = total_out / total_in * 100 if total_in else 0
        self.in_card.set_value(f"{total_in:.2f} <span style='font-size:14px;color:#9aa0ab;'>g</span>")
        self.out_card.set_value(f"{total_out:.2f} <span style='font-size:14px;color:#9aa0ab;'>g</span>")
        self.diff_card.set_value(f"{diff:+.2f} <span style='font-size:14px;color:#9aa0ab;'>g</span>"); self.diff_card.set_subtitle(f"수율 {yield_pct:.1f}%")

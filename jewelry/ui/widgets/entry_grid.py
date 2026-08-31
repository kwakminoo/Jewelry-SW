from __future__ import annotations

from PyQt6.QtCore import QDate, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPen
from PyQt6.QtWidgets import (
    QAbstractItemView, QHeaderView, QHBoxLayout, QPushButton, QStyledItemDelegate,
    QSizePolicy, QStyle, QTableWidget, QTableWidgetItem, QWidget,
)

from jewelry.ui.resources.icons import app_icon
from jewelry.ui.widgets.flat_scrollbar import FlatScrollBar
from jewelry.ui.widgets.photo_cell import PhotoThumbnail
from jewelry.ui.widgets.smooth_scroll import enable_smooth_scroll

KARATS = ["14K", "18K"]
_WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]
CHECKBOX_COL, DATE_COL, TIME_COL, PHOTO_COL = 0, 1, 2, 3
_KARAT_START = 4
COLUMN_MAP = {k: (4 + i * 3, 5 + i * 3, 6 + i * 3) for i, k in enumerate(KARATS)}
EDIT_COL = 10
TOTAL_COLUMNS = 11
HEADER_ROWS = 0  # compatibility: EntryGrid now contains data rows only.
INPUT_COL_TO_KARAT = {col: k for k, cols in COLUMN_MAP.items() for col in cols[:2]}

_HEADER_BG = QBrush(QColor("#f7f7f5"))
_TOTALS_BG = QBrush(QColor("#0a0a0a"))
_TEXT_DARK = QColor("#0a0a0a")
_TEXT_MUTED = QColor("#8a8a86")
_TEXT_WHITE = QColor("#ffffff")
DATA_ROW_HEIGHT = 39
TOTALS_ROW_HEIGHT = 37
HEADER_HEIGHT = 45
FIXED_WIDTHS = {CHECKBOX_COL: 38, DATE_COL: 124, TIME_COL: 80, PHOTO_COL: 54, EDIT_COL: 79}


class _TableDelegate(QStyledItemDelegate):
    GROUP_EDGES = {CHECKBOX_COL, PHOTO_COL, COLUMN_MAP["14K"][2], COLUMN_MAP["18K"][2]}

    def paint(self, painter, option, index) -> None:  # noqa: N802
        painter.save()
        bg = index.data(Qt.ItemDataRole.BackgroundRole)
        painter.fillRect(option.rect, bg if isinstance(bg, QBrush) else QBrush(QColor("#ffffff")))
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        if state is not None:
            hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
            self._paint_checkbox(painter, option.rect, state, hovered)
        else:
            painter.setPen((index.data(Qt.ItemDataRole.ForegroundRole) or QBrush(_TEXT_DARK)).color())
            font = index.data(Qt.ItemDataRole.FontRole)
            if isinstance(font, QFont): painter.setFont(font)
            align = index.data(Qt.ItemDataRole.TextAlignmentRole) or int(Qt.AlignmentFlag.AlignCenter)
            rect = option.rect.adjusted(14, 0, -8, 0) if int(align) & int(Qt.AlignmentFlag.AlignLeft) else option.rect
            painter.drawText(rect, int(align), index.data(Qt.ItemDataRole.DisplayRole) or "")
        painter.setPen(QPen(QColor("#e8e8e5"), 1))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        if index.column() in self.GROUP_EDGES:
            painter.setPen(QPen(QColor("#e2e2df"), 1))
            painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        painter.restore()

    @staticmethod
    def _paint_checkbox(painter, rect: QRect, state, hovered: bool) -> None:
        size = 16
        box = QRect(rect.center().x() - size // 2, rect.center().y() - size // 2, size, size)
        checked = state == Qt.CheckState.Checked or state == Qt.CheckState.Checked.value
        fill = "#333333" if checked and hovered else "#0a0a0a" if checked else "#f2f2f2" if hovered else "#ffffff"
        border = "#333333" if checked and hovered else "#0a0a0a" if checked else "#aeb4ba" if hovered else "#c7cbd0"
        painter.setBrush(QBrush(QColor(fill))); painter.setPen(QPen(QColor(border), 1))
        painter.drawRoundedRect(box, 2, 2)


class _StaticDelegate(_TableDelegate):
    """Header/total painter that understands merged group cells."""

    def paint(self, painter, option, index) -> None:  # noqa: N802
        super().paint(painter, option, index)
        if index.row() == 0 and index.column() in {COLUMN_MAP["14K"][0], COLUMN_MAP["18K"][0]}:
            painter.save(); painter.setPen(QPen(QColor("#e2e2df"), 1))
            painter.drawLine(option.rect.topRight(), option.rect.bottomRight()); painter.restore()


def _configure_columns(table: QTableWidget, stretch: bool) -> None:
    header = table.horizontalHeader()
    header.setMinimumSectionSize(0)
    for col in range(TOTAL_COLUMNS):
        if col in FIXED_WIDTHS:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(col, FIXED_WIDTHS[col])
        else:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch if stretch else QHeaderView.ResizeMode.Fixed)


class LedgerHeader(QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(2, TOTAL_COLUMNS, parent)
        self.horizontalHeader().hide(); self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.setShowGrid(False); self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True); self.viewport().setMouseTracking(True); self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(HEADER_HEIGHT)
        self.setItemDelegate(_StaticDelegate(self)); _configure_columns(self, False)
        self.setSpan(0, CHECKBOX_COL, 2, 1)
        check = self._item(""); check.setFlags(check.flags() | Qt.ItemFlag.ItemIsUserCheckable); check.setCheckState(Qt.CheckState.Unchecked)
        self.setItem(0, CHECKBOX_COL, check)
        for col, text in ((DATE_COL, "일자"), (TIME_COL, "시간"), (PHOTO_COL, "사진")):
            self.setSpan(0, col, 2, 1); self.setItem(0, col, self._item(text, muted=True))
        for karat in KARATS:
            inc, out, diff = COLUMN_MAP[karat]
            self.setSpan(0, inc, 1, 3); self.setItem(0, inc, self._item(karat))
            for col, text in ((inc, "입고"), (out, "출고"), (diff, "차익")): self.setItem(1, col, self._item(text, muted=True))
        self.setSpan(0, EDIT_COL, 2, 1); self.setItem(0, EDIT_COL, self._item("수정", muted=True))
        self.setRowHeight(0, 24); self.setRowHeight(1, 21)

    @staticmethod
    def _item(text: str, muted: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text); item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); item.setBackground(_HEADER_BG)
        item.setForeground(_TEXT_MUTED if muted else _TEXT_DARK); font = item.font(); font.setBold(True); item.setFont(font)
        return item

    def set_active(self, karat: str | None) -> None:
        for name, (inc, _out, _diff) in COLUMN_MAP.items():
            item = self.item(0, inc)
            item.setBackground(QBrush(QColor("#0a0a0a") if name == karat else QColor("#f7f7f5")))
            item.setForeground(_TEXT_WHITE if name == karat else _TEXT_DARK)


class FixedSummaryBar(QTableWidget):
    def __init__(self, grid: "EntryGrid", parent=None) -> None:
        super().__init__(1, TOTAL_COLUMNS, parent)
        self.grid = grid; self._period_label = ""
        self.horizontalHeader().hide(); self.verticalHeader().hide(); self.setShowGrid(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(TOTALS_ROW_HEIGHT)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(TOTALS_ROW_HEIGHT); self.setItemDelegate(_StaticDelegate(self)); _configure_columns(self, False)
        self.setSpan(0, CHECKBOX_COL, 1, 4); self.setItem(0, CHECKBOX_COL, self._item("합계", True))
        for cols in COLUMN_MAP.values():
            for col in cols: self.setItem(0, col, self._item("0.00"))
        self.setItem(0, EDIT_COL, self._item("")); self.setRowHeight(0, TOTALS_ROW_HEIGHT)

    @staticmethod
    def _item(text: str, left: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text); item.setFlags(Qt.ItemFlag.ItemIsEnabled); item.setBackground(_TOTALS_BG); item.setForeground(_TEXT_WHITE)
        item.setTextAlignment((Qt.AlignmentFlag.AlignLeft if left else Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter)
        font = item.font(); font.setBold(True); item.setFont(font); return item

    def set_period_label(self, label: str) -> None:
        self._period_label = label; self.refresh()

    def refresh(self) -> None:
        self.item(0, CHECKBOX_COL).setText(f"합계 · {self._period_label}" if self._period_label else "합계")
        for karat, (inc, out, diff) in COLUMN_MAP.items():
            total_in, total_out = self.grid.total_weight(karat, "in"), self.grid.total_weight(karat, "out")
            self.item(0, inc).setText(f"{total_in:.2f}"); self.item(0, out).setText(f"{total_out:.2f}"); self.item(0, diff).setText(f"{total_in-total_out:+.2f}")

    def sync_widths(self) -> None:
        for col in range(TOTAL_COLUMNS): self.setColumnWidth(col, self.grid.columnWidth(col))


class EntryGrid(QTableWidget):
    changed = pyqtSignal()

    def __init__(self, sample_rows: list[dict] | None = None, parent=None) -> None:
        super().__init__(0, TOTAL_COLUMNS, parent)
        self.category = ""  # set by ProcessTab after construction; shown in the edit dialog.
        self.horizontalHeader().hide(); self.verticalHeader().hide(); self.setShowGrid(False); self.setMinimumHeight(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBar(FlatScrollBar(Qt.Orientation.Vertical, self))
        enable_smooth_scroll(self)
        vertical = self.verticalHeader()
        vertical.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical.setDefaultSectionSize(DATA_ROW_HEIGHT)
        vertical.setMinimumSectionSize(DATA_ROW_HEIGHT)
        vertical.setMaximumSectionSize(DATA_ROW_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True); self.viewport().setMouseTracking(True); self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAlternatingRowColors(False); self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked)
        self.setItemDelegate(_TableDelegate(self)); _configure_columns(self, True)
        self.itemChanged.connect(self._on_item_changed)
        for data in sample_rows or []: self.add_row(data)
        self.scrollToTop()

    def add_row(self, data: dict | None = None) -> None:
        data = data or {}; row = self.rowCount(); self.blockSignals(True); self.insertRow(row); self.setRowHeight(row, DATA_ROW_HEIGHT)
        check = QTableWidgetItem(""); check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        check.setCheckState(Qt.CheckState.Checked if data.get("checked") else Qt.CheckState.Unchecked); self.setItem(row, CHECKBOX_COL, check)
        self.setItem(row, DATE_COL, self._date_item(self._format_date(data.get("date"))))
        self.setItem(row, TIME_COL, self._plain_item(data.get("time", "")))
        self.setItem(row, PHOTO_COL, self._plain_item("")); self.setCellWidget(row, PHOTO_COL, self._centered_cell(PhotoThumbnail(self)))
        for karat, (inc, out, diff) in COLUMN_MAP.items():
            for col, direction in ((inc, "in"), (out, "out")):
                value = data.get((karat, direction)); item = QTableWidgetItem("" if value is None else f"{value:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.setItem(row, col, item)
            self.setItem(row, diff, self._diff_item(0)); self._recalc_diff(row, karat)
        edit = QPushButton("수정", self); edit.setObjectName("rowEditButton"); edit.setFixedSize(55, 25)
        edit.setIcon(app_icon("edit")); edit.setIconSize(QSize(13, 13)); edit.clicked.connect(self._on_edit_clicked)
        self.setItem(row, EDIT_COL, self._plain_item("")); self.setCellWidget(row, EDIT_COL, self._centered_cell(edit))
        self._set_checked_row(row, bool(data.get("checked"))); self.blockSignals(False); self.changed.emit()

    @staticmethod
    def _centered_cell(control: QWidget) -> QWidget:
        wrapper = QWidget(); wrapper.setObjectName("tableCellWrapper"); layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(control, 0, Qt.AlignmentFlag.AlignCenter); return wrapper

    @staticmethod
    def _plain_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text); item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); item.setForeground(_TEXT_MUTED); return item

    @staticmethod
    def _date_item(text: str) -> QTableWidgetItem:
        item = EntryGrid._plain_item(text); font = item.font(); font.setPixelSize(12); font.setWeight(QFont.Weight.Medium)
        item.setFont(font); item.setForeground(_TEXT_DARK); return item

    @staticmethod
    def _diff_item(value: float) -> QTableWidgetItem:
        item = EntryGrid._plain_item(f"{value:+.2f}"); item.setForeground(_TEXT_DARK); font = item.font(); font.setBold(True); item.setFont(font); return item

    @staticmethod
    def _format_date(value: str | None) -> str:
        if not value: return ""
        date = QDate.fromString(value, "yyyy-MM-dd")
        return value if not date.isValid() else f"{date.year()}.{date.month():02d}.{date.day():02d} {_WEEKDAY_KR[date.dayOfWeek()-1]}"

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        row, col = item.row(), item.column()
        if col == CHECKBOX_COL: self._set_checked_row(row, item.checkState() == Qt.CheckState.Checked)
        if col in INPUT_COL_TO_KARAT: self._recalc_diff(row, INPUT_COL_TO_KARAT[col])
        self.changed.emit()

    def _set_checked_row(self, row: int, checked: bool) -> None:
        color = QColor("#f2f2ef" if checked else "#ffffff")
        for col in range(TOTAL_COLUMNS):
            if self.item(row, col): self.item(row, col).setBackground(QBrush(color))
        for col in (PHOTO_COL, EDIT_COL):
            widget = self.cellWidget(row, col)
            if widget: widget.setStyleSheet(f"QWidget#tableCellWrapper {{ background-color:{color.name()}; border:0; border-bottom:1px solid #e8e8e5; }}")

    def _on_edit_clicked(self) -> None:
        button = self.sender()
        for row in range(self.rowCount()):
            wrapper = self.cellWidget(row, EDIT_COL)
            if wrapper and wrapper.findChild(QPushButton) is button:
                self._open_detail_dialog(row); return

    def _open_detail_dialog(self, row: int) -> None:
        from jewelry.ui.widgets.entry_detail_dialog import EntryDetailDialog
        dialog = EntryDetailDialog(self.entry_snapshot(row), self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            result = dialog.result_values()
            self.apply_entry_edit(row, result["karat"], result["in"], result["out"], result["memo"])

    def _extra(self, row: int) -> dict:
        item = self.item(row, DATE_COL)
        data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            date, time = self.item(row, DATE_COL).text(), self.item(row, TIME_COL).text()
            digits = sum(ord(c) for c in f"{date}{time}") % 9000 + 1000
            data = {"record_id": f"JS-{digits:04d}", "memo": ""}
            item.setData(Qt.ItemDataRole.UserRole, data)
        return data

    def karat_values(self, row: int, karat: str) -> tuple[float, float]:
        inc, out, _ = COLUMN_MAP[karat]
        return self._cell_value(row, inc), self._cell_value(row, out)

    def set_karat_values(self, row: int, karat: str, in_value: float, out_value: float) -> None:
        inc, out, _ = COLUMN_MAP[karat]
        self.blockSignals(True)
        self.item(row, inc).setText(f"{in_value:.2f}"); self.item(row, out).setText(f"{out_value:.2f}")
        self.blockSignals(False)
        self._recalc_diff(row, karat); self.changed.emit()

    def entry_snapshot(self, row: int) -> dict:
        extra = self._extra(row)
        return {
            "row": row, "category": self.category, "karat": "14K",
            "date": self.item(row, DATE_COL).text(),
            "record_id": extra["record_id"], "memo": extra["memo"],
            "values": {karat: self.karat_values(row, karat) for karat in KARATS},
        }

    def apply_entry_edit(self, row: int, karat: str, in_value: float, out_value: float, memo: str) -> None:
        self.set_karat_values(row, karat, in_value, out_value)
        # item.data() can hand back a converted copy rather than the stored
        # object, so mutate-then-setData explicitly to persist the change.
        extra = self._extra(row)
        extra["memo"] = memo
        self.item(row, DATE_COL).setData(Qt.ItemDataRole.UserRole, extra)

    def _recalc_diff(self, row: int, karat: str) -> None:
        inc, out, diff = COLUMN_MAP[karat]; self.item(row, diff).setText(f"{self._cell_value(row, inc)-self._cell_value(row, out):+.2f}")

    def _cell_value(self, row: int, col: int) -> float:
        try: return float(self.item(row, col).text())
        except (AttributeError, ValueError): return 0.0

    def set_active(self, karat: str | None) -> None:
        pass  # Active karat is represented by the shared record button; header stays fixed.

    def total_weight(self, karat: str, direction: str) -> float:
        inc, out, _ = COLUMN_MAP[karat]; col = inc if direction == "in" else out
        return sum(self._cell_value(row, col) for row in range(self.rowCount()))

    def data_row_count(self) -> int: return self.rowCount()
    def selected_count(self) -> int:
        return sum(self.item(row, CHECKBOX_COL).checkState() == Qt.CheckState.Checked for row in range(self.rowCount()))

    def select_all(self, state: Qt.CheckState) -> None:
        self.blockSignals(True)
        for row in range(self.rowCount()): self.item(row, CHECKBOX_COL).setCheckState(state); self._set_checked_row(row, state == Qt.CheckState.Checked)
        self.blockSignals(False); self.changed.emit()

    def filter_rows(self, text: str) -> None:
        needle = text.strip().lower()
        for row in range(self.rowCount()):
            haystack = f"{self.item(row, DATE_COL).text()} {self.item(row, TIME_COL).text()}".lower()
            self.setRowHidden(row, bool(needle) and needle not in haystack)

    def show_selected_only(self) -> None:
        for row in range(self.rowCount()): self.setRowHidden(row, self.item(row, CHECKBOX_COL).checkState() != Qt.CheckState.Checked)

    def export_rows(self) -> list[list[str]]:
        rows = []
        for row in range(self.rowCount()):
            values = [self.item(row, DATE_COL).text(), self.item(row, TIME_COL).text()]
            for karat in KARATS: values.extend(self.item(row, col).text() for col in COLUMN_MAP[karat])
            rows.append(values)
        return rows

    def latest_entry_label(self) -> str | None:
        if not self.rowCount(): return None
        return f"{self.item(0, DATE_COL).text()} {self.item(0, TIME_COL).text()}".strip()

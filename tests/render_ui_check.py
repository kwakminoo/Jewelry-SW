"""Offscreen visual smoke check; also writes the inspection screenshot."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton

from jewelry.ui.widgets.entry_grid import CHECKBOX_COL, EDIT_COL, HEADER_ROWS, PHOTO_COL
from jewelry.ui.window.main_window import MainWindow


app = QApplication([])
qss = Path("jewelry/ui/resources/styles/theme.qss").read_text(encoding="utf-8")
app.setStyle("Fusion")
app.setStyleSheet(qss)
window = MainWindow()
window.resize(1440, 930)
window.show()
app.processEvents()

tab = window.pages.widget(0).tabs.currentWidget()
page = window.pages.widget(0)
grid = tab.grid
row = HEADER_ROWS
normal_row_heights = tuple(grid.rowHeight(index) for index in range(min(3, grid.rowCount())))
normal_viewport_height = grid.viewport().height()
assert normal_row_heights == (39, 39, 39)
photo_wrapper = grid.cellWidget(row, PHOTO_COL)
edit_wrapper = grid.cellWidget(row, EDIT_COL)
photo = photo_wrapper.findChild(QPushButton)
edit = edit_wrapper.findChild(QPushButton)

assert photo.geometry().center() == photo_wrapper.rect().center(), (photo.geometry(), photo_wrapper.rect())
assert edit.geometry().center() == edit_wrapper.rect().center(), (edit.geometry(), edit_wrapper.rect())
assert tab.selection_label.isVisible() and tab.autosave_label.isVisible()
assert tab.selection_label.geometry().bottom() <= tab.height()
assert tab.total_bar.isVisible() and tab.header.isVisible()

action_ids = tuple(id(widget) for widget in (page.search_input, page.filter_button, page.export_button, page.record_btn))
for index in (1, 0, 1, 0, 1, 0):
    page.tab_bar.setCurrentIndex(index)
    app.processEvents()
    assert all(widget.isVisible() for widget in (page.search_input, page.filter_button, page.export_button, page.record_btn))
    assert action_ids == tuple(id(widget) for widget in (page.search_input, page.filter_button, page.export_button, page.record_btn))
tab = page.tabs.currentWidget()
grid = tab.grid

def checkbox_pixel(target_grid, target_row):
    rect = target_grid.visualItemRect(target_grid.item(target_row, CHECKBOX_COL))
    point = target_grid.viewport().mapTo(window, rect.center())
    color = window.grab().toImage().pixelColor(point)
    return color.red(), color.green(), color.blue(), rect.center()

checked_rgb = checkbox_pixel(grid, 0)[:3]
unchecked_rgb = checkbox_pixel(grid, 1)[:3]
assert max(checked_rgb) < 40, checked_rgb
assert min(unchecked_rgb) > 220, unchecked_rgb
checked_center = checkbox_pixel(grid, 0)[3]
QTest.mouseMove(grid.viewport(), checked_center); app.processEvents()
hover_rgb = checkbox_pixel(grid, 0)[:3]
assert min(hover_rgb) > min(checked_rgb) and max(hover_rgb) < 90, (checked_rgb, hover_rgb)
QTest.mouseMove(grid.viewport(), grid.viewport().rect().bottomRight()); app.processEvents()

check = grid.item(row + 1, CHECKBOX_COL)
check.setCheckState(Qt.CheckState.Checked)
app.processEvents()
expected = "#f2f2ef"
assert grid.item(row + 1, 1).background().color().name() == expected
assert expected in grid.cellWidget(row + 1, PHOTO_COL).styleSheet()
assert expected in grid.cellWidget(row + 1, EDIT_COL).styleSheet()
check.setCheckState(Qt.CheckState.Unchecked)
app.processEvents()
assert grid.item(row + 1, 1).background().color().name() == "#ffffff"
assert "#ffffff" in grid.cellWidget(row + 1, PHOTO_COL).styleSheet()

window.resize(1920, 1080)
app.processEvents()
large_row_heights = tuple(grid.rowHeight(index) for index in range(3))
large_viewport_height = grid.viewport().height()
assert large_row_heights == normal_row_heights
assert large_viewport_height > normal_viewport_height
assert tab.selection_label.isVisible() and tab.autosave_label.isVisible()
assert tab.selection_label.mapTo(window, tab.selection_label.rect().bottomLeft()).y() < window.height()
for _ in range(100): grid.add_row({"date": "2026-08-01", "time": "12:00"})
grid.scrollToBottom(); app.processEvents()
assert tab.header.isVisible() and tab.total_bar.isVisible()
for col in range(grid.columnCount()):
    assert tab.header.columnWidth(col) == grid.columnWidth(col)
    assert tab.total_bar.columnWidth(col) == grid.columnWidth(col)
assert tab.total_bar.mapTo(window, tab.total_bar.rect().bottomLeft()).y() < window.height()
assert tab.selection_label.mapTo(window, tab.selection_label.rect().bottomLeft()).y() < window.height()
window.title_bar.maximize_button.click()
app.processEvents()
window.title_bar.update_maximize_icon()
maximized_row_heights = tuple(grid.rowHeight(index) for index in range(3))
assert maximized_row_heights == normal_row_heights
assert window.title_bar.maximize_button.property("windowStateIcon") == "restore"
assert tab.selection_label.isVisible() and tab.autosave_label.isVisible()
assert tab.selection_label.mapTo(window, tab.selection_label.rect().bottomLeft()).y() < window.height()
total_top = tab.total_bar.mapTo(window, tab.total_bar.rect().topLeft()).y()
total_bottom = tab.total_bar.mapTo(window, tab.total_bar.rect().bottomLeft()).y()
print(f"max_size={window.width()}x{window.height()} grid={tab.grid.geometry().getRect()} total={tab.total_bar.geometry().getRect()} footer={tab.selection_label.parentWidget().geometry().getRect()}", flush=True)
assert tab.total_bar.height() >= 37 and 0 <= total_top < total_bottom < window.height()
central = window.centralWidget()
page = window.pages.currentWidget()
available = window.screen().availableGeometry()
frame = window.frameGeometry()
assert frame.left() >= available.left() and frame.top() >= available.top()
assert frame.right() <= available.right() and frame.bottom() <= available.bottom()
process_height = tab.header.height() + tab.grid.height() + tab.total_bar.height() + tab.selection_label.parentWidget().height()
assert process_height == tab.height()
assert tab.grid.viewport().height() > 0
print(
    f"heights window={window.height()} central={central.height()} page={page.height()} "
    f"process={tab.height()} grid={tab.grid.height()} viewport={tab.grid.viewport().height()} "
    f"total={tab.total_bar.height()} footer={tab.selection_label.parentWidget().height()} "
    f"available={available.getRect()} frame={frame.getRect()}", flush=True,
)
maximized_output = Path("ui-check-maximized.png").resolve()
assert window.grab().save(str(maximized_output))
window.title_bar.maximize_button.click()
app.processEvents()
window.title_bar.update_maximize_icon()
restored_row_heights = tuple(grid.rowHeight(index) for index in range(3))
assert restored_row_heights == normal_row_heights
assert window.title_bar.maximize_button.property("windowStateIcon") == "maximize"
window.title_bar.maximize_button.click(); app.processEvents()
assert tuple(grid.rowHeight(index) for index in range(3)) == normal_row_heights
window.title_bar.maximize_button.click(); app.processEvents()
assert tuple(grid.rowHeight(index) for index in range(3)) == normal_row_heights
for width, height in ((1120, 720), (1280, 800), (1440, 930), (1200, 760), (1600, 1000)):
    window.resize(width, height); app.processEvents()
    assert tuple(grid.rowHeight(index) for index in range(3)) == normal_row_heights
    assert tab.total_bar.mapTo(window, tab.total_bar.rect().bottomLeft()).y() < window.height()
    assert tab.footer.mapTo(window, tab.footer.rect().bottomLeft()).y() < window.height()
window.resize(1440, 930)
app.processEvents()

output = Path("ui-check.png").resolve()
saved = window.grab().save(str(output))
assert saved
print(f"screenshot={output}")
print(f"window={window.size().width()}x{window.size().height()}")
print(f"rows normal={normal_row_heights} large={large_row_heights} maximized={maximized_row_heights} restored={restored_row_heights}")
print(f"viewports normal={normal_viewport_height} large={large_viewport_height}")
print(f"footer_y={tab.selection_label.mapTo(window, tab.selection_label.rect().topLeft()).y()}")
print(f"photo={photo.geometry().getRect()} wrapper={photo_wrapper.rect().getRect()}")
print(f"edit={edit.geometry().getRect()} wrapper={edit_wrapper.rect().getRect()}")
print("columns=" + ",".join(f"{grid.columnViewportPosition(c)}:{grid.columnWidth(c)}" for c in range(grid.columnCount())))
window.close()

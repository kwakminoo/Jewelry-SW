from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

from jewelry.config.settings import APP_NAME, CAPTURES_DIR, DATA_DIR
from jewelry.ui.widgets.flat_scrollbar import FlatScrollBar
from jewelry.ui.widgets.info_dialog import InfoDialog
from jewelry.ui.widgets.smooth_scroll import enable_smooth_scroll

# 저울/카메라 장비 목록. 실제 장치 연동 전 화면 확인용 샘플 값이다.
DEVICES = [
    {"name": "CAS SW-1", "type": "저울", "conn": "USB", "port": "COM3", "baud": "9600", "status": "정상", "last_seen": "12:42:15"},
    {"name": "CAM-01", "type": "카메라", "conn": "USB", "port": "-", "baud": "-", "status": "정상", "last_seen": "12:41:02"},
]


class SettingsPage(QWidget):
    SECTIONS = ["일반", "계산 규칙", "단위 · 형식", "설비", "내보내기", "백업"]

    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("page")
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        shell = QFrame(); shell.setObjectName("settingsShell"); row = QHBoxLayout(shell)
        row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)
        self.nav = QListWidget(); self.nav.setObjectName("settingsNav"); self.nav.setFixedWidth(180)
        self.nav.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.nav.setVerticalScrollBar(FlatScrollBar(Qt.Orientation.Vertical, self.nav)); enable_smooth_scroll(self.nav)
        for name in self.SECTIONS: QListWidgetItem(name, self.nav)
        row.addWidget(self.nav); self.stack = QStackedWidget()
        for page in (self._general(), self._calculation(), self._format(), self._equipment(), self._export(), self._backup()): self.stack.addWidget(page)
        row.addWidget(self.stack, 1); outer.addWidget(shell, 1)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex); self.nav.setCurrentRow(1)

    def _page(self, title, help_text):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(28, 24, 28, 24); layout.setSpacing(14)
        heading = QLabel(title); heading.setObjectName("sectionTitle"); layout.addWidget(heading)
        hint = QLabel(help_text); hint.setObjectName("mutedText"); layout.addWidget(hint); return page, layout

    def _footer(self, layout):
        layout.addStretch(1); line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); layout.addWidget(line)
        actions = QHBoxLayout(); actions.addStretch(1); reset = QPushButton("기본값 복원"); save = QPushButton("변경 저장"); save.setObjectName("primaryButton")
        reset.clicked.connect(lambda: InfoDialog.show_message(self, "설정", "기본값으로 복원했습니다.")); save.clicked.connect(lambda: InfoDialog.show_message(self, "설정", "설정을 저장했습니다."))
        actions.addWidget(reset); actions.addWidget(save); layout.addLayout(actions)

    def _general(self):
        page, layout = self._page("일반", "앱의 기본 동작을 설정합니다."); form = QFormLayout()
        form.addRow("프로그램 이름", QLineEdit(APP_NAME))
        path_row = QHBoxLayout(); path_row.setSpacing(8)
        data_path_input = QLineEdit(str(DATA_DIR)); path_row.addWidget(data_path_input, 1)
        browse_btn = QPushButton("찾아보기"); browse_btn.setObjectName("entrySecondaryButton")
        browse_btn.clicked.connect(lambda: self._browse_folder(data_path_input)); path_row.addWidget(browse_btn)
        form.addRow("데이터 저장 경로", path_row)
        form.addRow("작업자 이름", self._combo(["관리자", "작업자 1", "작업자 2"])); form.addRow("시작 화면", self._combo(["메인", "설비", "설정"])); layout.addLayout(form); self._footer(layout); return page

    def _browse_folder(self, line_edit: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(self, "폴더 선택", line_edit.text())
        if path: line_edit.setText(path)

    def _equipment(self):
        page, layout = self._page("설비", "연결된 저울과 카메라를 관리합니다.")

        default_form = QFormLayout(); default_form.setVerticalSpacing(16)
        default_form.addRow("기본 저울", self._combo([d["name"] for d in DEVICES if d["type"] == "저울"]))
        default_form.addRow("기본 카메라", self._combo([d["name"] for d in DEVICES if d["type"] == "카메라"]))
        default_form.addRow("사진 저장 경로", QLineEdit(str(CAPTURES_DIR)))
        layout.addLayout(default_form)

        divider = QFrame(); divider.setObjectName("appDialogDivider"); divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        split = QHBoxLayout(); split.setSpacing(16)

        self.device_table = QTableWidget(len(DEVICES), 5)
        self.device_table.setHorizontalHeaderLabels(["장비명", "종류", "연결", "포트", "상태"])
        self.device_table.verticalHeader().hide()
        self.device_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.device_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.device_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.device_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.device_table.setVerticalScrollBar(FlatScrollBar(Qt.Orientation.Vertical, self.device_table))
        enable_smooth_scroll(self.device_table)
        for row, device in enumerate(DEVICES):
            for col, key in enumerate(("name", "type", "conn", "port", "status")):
                item = QTableWidgetItem(device[key]); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.device_table.setItem(row, col, item)
        self.device_table.currentCellChanged.connect(self._on_device_selected)
        split.addWidget(self.device_table, 3)

        self.device_detail_frame = QFrame(); self.device_detail_frame.setObjectName("deviceCard")
        detail_layout = QVBoxLayout(self.device_detail_frame)
        detail_layout.setContentsMargins(22, 20, 22, 20); detail_layout.setSpacing(12)
        detail_title = QLabel("장비 정보"); detail_title.setObjectName("sectionTitle"); detail_layout.addWidget(detail_title)
        self.device_form = QFormLayout(); self.device_form.setVerticalSpacing(10)
        detail_layout.addLayout(self.device_form); detail_layout.addStretch(1)
        split.addWidget(self.device_detail_frame, 2)

        layout.addLayout(split, 1)
        if DEVICES: self.device_table.selectRow(0)
        return page

    def _on_device_selected(self, row: int, *_args) -> None:
        if row < 0 or row >= len(DEVICES): return
        device = DEVICES[row]
        while self.device_form.rowCount(): self.device_form.removeRow(0)
        self.device_form.addRow("이름", QLabel(device["name"]))
        self.device_form.addRow("종류", QLabel("전자저울" if device["type"] == "저울" else device["type"]))
        self.device_form.addRow("포트", QLabel(device["port"]))
        self.device_form.addRow("Baud Rate", QLabel(device["baud"]))
        status_label = QLabel(device["status"]); status_label.setObjectName("statusBadge")
        if device["status"] == "정상":
            status_label.setProperty("connected", True)
            status_label.style().unpolish(status_label); status_label.style().polish(status_label)
        self.device_form.addRow("상태", status_label)
        self.device_form.addRow("마지막 통신", QLabel(device["last_seen"]))

    def _calculation(self):
        page, layout = self._page("계산 규칙", "수율과 차익 계산 및 반올림 방식을 조합합니다."); form = QFormLayout(); form.setVerticalSpacing(16)
        form.addRow("차익 계산 기준", self._combo(["입고 - 출고", "출고 - 입고"])); decimals = QSpinBox(); decimals.setRange(0, 4); decimals.setValue(2); decimals.setSuffix(" 자리")
        form.addRow("소수점 처리", decimals); form.addRow("반올림", self._combo(["사사오입", "올림", "버림"])); form.addRow("기본 순도", self._combo(["14K", "18K", "24K"])); layout.addLayout(form); self._footer(layout); return page

    def _format(self):
        page, layout = self._page("단위 · 형식", "화면과 내보내기에 사용할 표시 형식입니다."); form = QFormLayout(); form.addRow("무게 단위", self._combo(["g", "돈"])); form.addRow("날짜 형식", self._combo(["YYYY.MM.DD", "YYYY-MM-DD"])); layout.addLayout(form); self._footer(layout); return page

    def _export(self):
        page, layout = self._page("내보내기", "CSV 파일에 포함할 기본 항목을 선택합니다.")
        for label in ("사진 경로 포함", "메모 포함", "선택한 기록만 내보내기"): layout.addWidget(QCheckBox(label))
        self._footer(layout); return page

    def _backup(self):
        page, layout = self._page("백업", "기록을 로컬 폴더에 안전하게 보관합니다."); enabled = QCheckBox("자동 백업 사용"); enabled.setChecked(True); layout.addWidget(enabled)
        form = QFormLayout(); form.addRow("주기", self._combo(["매일", "매주", "매월"])); layout.addLayout(form); self._footer(layout); return page

    @staticmethod
    def _combo(items):
        combo = QComboBox(); combo.addItems(items); return combo

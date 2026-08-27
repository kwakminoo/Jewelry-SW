from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSpinBox,
    QStackedWidget, QVBoxLayout, QWidget)


class SettingsPage(QWidget):
    SECTIONS = ["일반", "계산 규칙", "단위 · 형식", "내보내기", "백업"]

    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("page")
        outer = QVBoxLayout(self); outer.setContentsMargins(34, 28, 34, 28); outer.setSpacing(18)
        title = QLabel("설정"); title.setObjectName("pageTitle"); outer.addWidget(title)
        shell = QFrame(); shell.setObjectName("settingsShell"); row = QHBoxLayout(shell)
        row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)
        self.nav = QListWidget(); self.nav.setObjectName("settingsNav"); self.nav.setFixedWidth(180)
        for name in self.SECTIONS: QListWidgetItem(name, self.nav)
        row.addWidget(self.nav); self.stack = QStackedWidget()
        for page in (self._general(), self._calculation(), self._format(), self._export(), self._backup()): self.stack.addWidget(page)
        row.addWidget(self.stack, 1); outer.addWidget(shell, 1)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex); self.nav.setCurrentRow(1)

    def _page(self, title, help_text):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(28, 24, 28, 24); layout.setSpacing(14)
        heading = QLabel(title); heading.setObjectName("sectionTitle"); layout.addWidget(heading)
        hint = QLabel(help_text); hint.setObjectName("mutedText"); layout.addWidget(hint); return page, layout

    def _footer(self, layout):
        layout.addStretch(1); line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); layout.addWidget(line)
        actions = QHBoxLayout(); actions.addStretch(1); reset = QPushButton("기본값 복원"); save = QPushButton("변경 저장"); save.setObjectName("primaryButton")
        reset.clicked.connect(lambda: QMessageBox.information(self, "설정", "기본값으로 복원했습니다.")); save.clicked.connect(lambda: QMessageBox.information(self, "설정", "설정을 저장했습니다."))
        actions.addWidget(reset); actions.addWidget(save); layout.addLayout(actions)

    def _general(self):
        page, layout = self._page("일반", "앱의 기본 동작을 설정합니다."); form = QFormLayout()
        form.addRow("작업자 이름", self._combo(["관리자", "작업자 1", "작업자 2"])); form.addRow("시작 화면", self._combo(["메인", "장비 연결", "설정"])); layout.addLayout(form); self._footer(layout); return page

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

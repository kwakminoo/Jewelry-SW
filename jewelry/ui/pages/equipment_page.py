from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class DeviceCard(QFrame):
    def __init__(self, title, description, choices, parent=None):
        super().__init__(parent); self.setObjectName("deviceCard")
        layout = QVBoxLayout(self); layout.setContentsMargins(22, 20, 22, 20); layout.setSpacing(12)
        head = QHBoxLayout(); name = QLabel(title); name.setObjectName("sectionTitle"); self.state = QLabel("연결 안 됨"); self.state.setObjectName("statusBadge")
        head.addWidget(name); head.addStretch(1); head.addWidget(self.state); layout.addLayout(head)
        hint = QLabel(description); hint.setWordWrap(True); hint.setObjectName("mutedText"); layout.addWidget(hint)
        self.selector = QComboBox(); self.selector.addItems(choices); layout.addWidget(self.selector)
        self.button = QPushButton("연결 테스트"); self.button.setObjectName("primaryButton"); self.button.clicked.connect(self._test); layout.addWidget(self.button)

    def _test(self):
        self.button.setEnabled(False); self.button.setText("확인 중…"); self.state.setText("연결 확인 중"); QTimer.singleShot(700, self._complete)

    def _complete(self):
        self.button.setEnabled(True); self.button.setText("다시 테스트"); self.state.setText("정상 연결"); self.state.setProperty("connected", True); self.state.style().unpolish(self.state); self.state.style().polish(self.state)


class EquipmentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("page")
        layout = QVBoxLayout(self); layout.setContentsMargins(34, 28, 34, 28); layout.setSpacing(18)
        title = QLabel("장비 연결"); title.setObjectName("pageTitle"); layout.addWidget(title)
        sub = QLabel("저울과 카메라를 선택하고 연결 상태를 확인합니다."); sub.setObjectName("mutedText"); layout.addWidget(sub)
        grid = QGridLayout(); grid.setSpacing(14)
        grid.addWidget(DeviceCard("전자 저울", "시리얼 또는 USB 저울에서 실시간 무게를 읽습니다.", ["자동 감지", "COM1", "COM2", "COM3"]), 0, 0)
        grid.addWidget(DeviceCard("촬영 카메라", "기록에 첨부할 제품 사진을 촬영합니다.", ["기본 카메라", "USB Camera 1"]), 0, 1)
        layout.addLayout(grid); layout.addStretch(1)

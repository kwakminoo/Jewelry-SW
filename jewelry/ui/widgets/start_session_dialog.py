from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QWidget


class StartSessionDialog(QDialog):
    """시작 버튼을 누르면 뜨는 공정(광/연마) · 카라트(14K/18K) 선택 창."""

    CATEGORIES = ["광", "연마"]
    KARATS = ["14K", "18K"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("작업 시작")

        layout = QFormLayout(self)

        self.category_combo = QComboBox(self)
        self.category_combo.addItems(self.CATEGORIES)
        layout.addRow("공정", self.category_combo)

        self.karat_combo = QComboBox(self)
        self.karat_combo.addItems(self.KARATS)
        layout.addRow("카라트", self.karat_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def selection(self) -> tuple[str, str]:
        return self.category_combo.currentText(), self.karat_combo.currentText()

    @classmethod
    def get_selection(cls, parent: QWidget | None = None) -> tuple[str, str] | None:
        dialog = cls(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selection()
        return None

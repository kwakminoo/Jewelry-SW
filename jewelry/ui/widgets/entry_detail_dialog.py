from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from jewelry.ui.resources.icons import app_icon

KARATS = ["14K", "18K"]
CATEGORIES = ["광", "연마"]


class EntryDetailDialog(QDialog):
    """수정 버튼을 누르면 뜨는 기록 상세/편집 창."""

    def __init__(self, snapshot: dict, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("appDialogShell")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(500)
        self._snapshot = snapshot
        self._drag_origin: QPoint | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1); outer.setSpacing(0)
        outer.addWidget(self._build_title_bar(snapshot["record_id"]))

        body = QWidget(self); body.setObjectName("appDialogBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16); body_layout.setSpacing(14)

        body_layout.addLayout(self._build_header_row())

        grams_row = QHBoxLayout(); grams_row.setSpacing(14)
        self.in_input = self._build_gram_field("입고 (g)", grams_row)
        self.out_input = self._build_gram_field("출고 (g)", grams_row)
        body_layout.addLayout(grams_row)
        self.in_input.textChanged.connect(self._update_diff)
        self.out_input.textChanged.connect(self._update_diff)

        combo_row = QHBoxLayout(); combo_row.setSpacing(14)
        self.category_combo = self._build_combo_field("공정", CATEGORIES, snapshot["category"], combo_row)
        self.karat_combo = self._build_combo_field("순도", KARATS, snapshot["karat"], combo_row)
        self.category_combo.currentTextChanged.connect(self._update_subtitle)
        self.karat_combo.currentTextChanged.connect(self._on_karat_changed)
        body_layout.addLayout(combo_row)

        body_layout.addWidget(self._build_memo_field(snapshot["memo"]))

        divider = QFrame(body); divider.setObjectName("appDialogDivider"); divider.setFrameShape(QFrame.Shape.HLine)
        body_layout.addWidget(divider)

        body_layout.addLayout(self._build_footer_row())
        outer.addWidget(body)

        self._load_values(snapshot["karat"])

    # ------------------------------------------------------------ 조립
    def _build_title_bar(self, record_id: str) -> QFrame:
        frame = QFrame(self); frame.setObjectName("appDialogTitleBar"); frame.setFixedHeight(48)
        row = QHBoxLayout(frame); row.setContentsMargins(20, 0, 8, 0); row.setSpacing(0)
        self.title_label = QLabel(f"기록 상세 · {record_id}", frame); self.title_label.setObjectName("appDialogTitle")
        row.addWidget(self.title_label); row.addStretch(1)
        close_btn = QPushButton(frame); close_btn.setObjectName("appDialogClose")
        close_btn.setIcon(app_icon("window-close")); close_btn.clicked.connect(self.reject)
        row.addWidget(close_btn)
        return frame

    def _build_header_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(14)

        self.photo_box = QLabel(self); self.photo_box.setObjectName("entryPhotoBox")
        self.photo_box.setFixedSize(76, 76); self.photo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_box.setPixmap(app_icon("photo").pixmap(24, 24))
        row.addWidget(self.photo_box)

        info_col = QVBoxLayout(); info_col.setSpacing(8); info_col.addStretch(1)
        self.meta_label = QLabel(self); self.meta_label.setObjectName("entryItemMeta")
        info_col.addWidget(self.meta_label)
        photo_btn_row = QHBoxLayout(); photo_btn_row.setSpacing(6)
        replace_btn = QPushButton("사진 교체", self); replace_btn.setObjectName("entrySecondaryButton")
        delete_btn = QPushButton("삭제", self); delete_btn.setObjectName("entrySecondaryButton"); delete_btn.setEnabled(False)
        photo_btn_row.addWidget(replace_btn); photo_btn_row.addWidget(delete_btn); photo_btn_row.addStretch(1)
        info_col.addLayout(photo_btn_row)
        info_col.addStretch(1)
        row.addLayout(info_col, 1)
        return row

    def _build_gram_field(self, label_text: str, row: QHBoxLayout) -> QLineEdit:
        col = QVBoxLayout(); col.setSpacing(6)
        label = QLabel(label_text, self); label.setObjectName("dialogFieldLabel")
        col.addWidget(label)
        field = QLineEdit(self); field.setObjectName("entryGramInput")
        field.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        col.addWidget(field)
        row.addLayout(col, 1)
        return field

    def _build_combo_field(self, label_text: str, options: list[str], current: str, row: QHBoxLayout) -> QComboBox:
        col = QVBoxLayout(); col.setSpacing(6)
        label = QLabel(label_text, self); label.setObjectName("dialogFieldLabel")
        col.addWidget(label)
        combo = QComboBox(self); combo.setObjectName("dialogFieldCombo")
        combo.addItems(options)
        if current in options: combo.setCurrentText(current)
        col.addWidget(combo)
        row.addLayout(col, 1)
        return combo

    def _build_memo_field(self, memo: str) -> QWidget:
        wrap = QWidget(self); col = QVBoxLayout(wrap); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(6)
        label = QLabel("메모", self); label.setObjectName("dialogFieldLabel")
        col.addWidget(label)
        self.memo_input = QPlainTextEdit(self); self.memo_input.setObjectName("entryMemoInput")
        self.memo_input.setPlainText(memo); self.memo_input.setPlaceholderText("손실률 확인 필요")
        self.memo_input.setFixedHeight(48)
        col.addWidget(self.memo_input)
        return wrap

    def _build_footer_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(10)
        diff_col = QVBoxLayout(); diff_col.setSpacing(2)
        diff_label = QLabel("차익", self); diff_label.setObjectName("entryDiffLabel")
        diff_col.addWidget(diff_label)
        value_row = QHBoxLayout(); value_row.setSpacing(6)
        self.diff_value = QLabel(self); self.diff_value.setObjectName("entryDiffValue")
        value_row.addWidget(self.diff_value)
        self.diff_meta = QLabel(self); self.diff_meta.setObjectName("entryDiffMeta")
        value_row.addWidget(self.diff_meta); value_row.addStretch(1)
        diff_col.addLayout(value_row)
        row.addLayout(diff_col); row.addStretch(1)

        cancel_btn = QPushButton("취소", self); cancel_btn.setObjectName("dialogCancelButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("저장", self); save_btn.setObjectName("dialogPrimaryButton")
        save_btn.clicked.connect(self._on_save)
        row.addWidget(cancel_btn); row.addWidget(save_btn)
        return row

    # ------------------------------------------------------------ 동작
    def _load_values(self, karat: str) -> None:
        in_value, out_value = self._snapshot["values"][karat]
        self.in_input.setText(f"{in_value:.2f}"); self.out_input.setText(f"{out_value:.2f}")
        self._update_subtitle()

    def _on_karat_changed(self, karat: str) -> None:
        self._load_values(karat)

    def _update_subtitle(self, *_args) -> None:
        date_only = self._snapshot["date"].split()[0] if self._snapshot["date"] else ""
        self.meta_label.setText(f"{self.karat_combo.currentText()} · {self.category_combo.currentText()} · {date_only}")

    def _parsed(self, field: QLineEdit) -> float:
        try: return float(field.text())
        except ValueError: return 0.0

    def _update_diff(self, *_args) -> None:
        in_value, out_value = self._parsed(self.in_input), self._parsed(self.out_input)
        diff = in_value - out_value
        pct = (diff / in_value * 100) if in_value else 0.0
        self.diff_value.setText(f"{diff:+.2f}")
        self.diff_meta.setText(f"g · {pct:.1f}%")

    def _on_save(self) -> None:
        self.accept()

    def result_values(self) -> dict:
        return {
            "karat": self.karat_combo.currentText(),
            "in": self._parsed(self.in_input),
            "out": self._parsed(self.out_input),
            "memo": self.memo_input.toPlainText(),
        }

    # ------------------------------------------------------------ 창 이동 (frameless)
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 48:
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None

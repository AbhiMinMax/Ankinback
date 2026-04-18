from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QTextEdit, QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut


class MainPopup(QDialog):
    def __init__(self, tracker, quiz_engine, session_log, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.quiz_engine = quiz_engine
        self.session_log = session_log
        self._list_visible = False
        self._session_correct = 0
        self._session_total = 0
        self._manual_quiz_callback = None
        self._setup_ui()
        self._setup_shortcuts()
        self.setWindowTitle("WM Trainer")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(360, 220)

    def _setup_ui(self):
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Span (N):"))
        self.n_spin = QSpinBox()
        self.n_spin.setRange(1, 20)
        self.n_spin.setValue(5)
        row1.addWidget(self.n_spin)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto", "Manual"])
        row1.addWidget(self.mode_combo)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.trigger_btn = QPushButton("Quiz [Shift+Q]")
        self.trigger_btn.setVisible(False)
        self.show_btn = QPushButton("Show [Shift+S]")
        self.clear_btn = QPushButton("Clear [Shift+C]")
        row2.addWidget(self.trigger_btn)
        row2.addWidget(self.show_btn)
        row2.addWidget(self.clear_btn)
        layout.addLayout(row2)

        self.score_label = QLabel("Session: 0 / 0")
        self.score_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.score_label)

        self.start_btn = QPushButton("Start Session")
        self.start_btn.setStyleSheet("padding: 6px; font-weight: bold;")
        self.start_btn.clicked.connect(self.hide)
        layout.addWidget(self.start_btn)

        self.list_area = QTextEdit()
        self.list_area.setReadOnly(True)
        self.list_area.setVisible(False)
        self.list_area.setMinimumHeight(200)
        layout.addWidget(self.list_area)

        self.setLayout(layout)

        self.show_btn.clicked.connect(self._on_toggle_show)
        self.clear_btn.clicked.connect(self._on_clear)
        self.trigger_btn.clicked.connect(self._on_manual_quiz)
        self.mode_combo.currentTextChanged.connect(self._on_mode_change)
        self.n_spin.valueChanged.connect(self.refresh)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Shift+S"), self, self._on_toggle_show)
        QShortcut(QKeySequence("Shift+C"), self, self._on_clear)
        QShortcut(QKeySequence("Shift+Q"), self, self._on_manual_quiz)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def _on_toggle_show(self):
        self._list_visible = not self._list_visible
        self.list_area.setVisible(self._list_visible)
        self.show_btn.setText("Hide [Shift+S]" if self._list_visible else "Show [Shift+S]")
        self.adjustSize()
        if self._list_visible:
            self.refresh()

    def _on_clear(self):
        self.tracker.clear()
        self._session_correct = 0
        self._session_total = 0
        self._update_score()
        self.refresh()

    def _on_mode_change(self, mode: str):
        self.trigger_btn.setVisible(mode == "Manual")

    def _on_manual_quiz(self):
        if self._manual_quiz_callback:
            self._manual_quiz_callback()

    def set_manual_quiz_callback(self, callback):
        self._manual_quiz_callback = callback

    def get_n(self) -> int:
        return self.n_spin.value()

    def is_auto_mode(self) -> bool:
        return self.mode_combo.currentText() == "Auto"

    def record_answer(self, correct: bool):
        self._session_total += 1
        if correct:
            self._session_correct += 1
        self._update_score()

    def _update_score(self):
        total = self._session_total
        correct = self._session_correct
        pct = f" ({int(correct / total * 100)}%)" if total > 0 else ""
        self.score_label.setText(f"Session: {correct} / {total}{pct}")

    def refresh(self):
        if self._list_visible:
            entries = self.tracker.get_last_n(self.get_n())
            self.list_area.setPlainText('\n'.join(
                f"{i + 1}. {e}" for i, e in enumerate(entries)
            ))

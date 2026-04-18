from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QTextEdit, QComboBox, QFrame,
)
from PyQt6.QtCore import Qt, QTimer
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
        self._quiz_question = None
        self._quiz_callback = None
        self._quiz_answered = False
        self._auto_shown = False
        self._setup_ui()
        self._setup_shortcuts()
        self.setWindowTitle("WM Trainer")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(360, 200)

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Config panel
        self.config_frame = QFrame()
        config_layout = QVBoxLayout(self.config_frame)
        config_layout.setContentsMargins(0, 0, 0, 0)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Span (N):"))
        self.n_spin = QSpinBox()
        self.n_spin.setRange(1, 20)
        self.n_spin.setValue(5)
        row1.addWidget(self.n_spin)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto", "Manual"])
        row1.addWidget(self.mode_combo)
        config_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.trigger_btn = QPushButton("Quiz [Shift+Q]")
        self.trigger_btn.setVisible(False)
        self.show_btn = QPushButton("Show [Shift+S]")
        self.clear_btn = QPushButton("Clear [Shift+C]")
        row2.addWidget(self.trigger_btn)
        row2.addWidget(self.show_btn)
        row2.addWidget(self.clear_btn)
        config_layout.addLayout(row2)

        self.score_label = QLabel("Session: 0 / 0")
        self.score_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        config_layout.addWidget(self.score_label)

        self.start_btn = QPushButton("Start Session")
        self.start_btn.setStyleSheet("padding: 6px; font-weight: bold;")
        self.start_btn.clicked.connect(self.hide)
        config_layout.addWidget(self.start_btn)

        self.list_area = QTextEdit()
        self.list_area.setReadOnly(True)
        self.list_area.setVisible(False)
        self.list_area.setMinimumHeight(200)
        config_layout.addWidget(self.list_area)

        layout.addWidget(self.config_frame)

        # Quiz panel (hidden until a quiz fires)
        self.quiz_frame = QFrame()
        quiz_layout = QVBoxLayout(self.quiz_frame)
        quiz_layout.setContentsMargins(0, 0, 0, 0)

        self.quiz_prompt_label = QLabel()
        self.quiz_prompt_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        self.quiz_prompt_label.setWordWrap(True)
        quiz_layout.addWidget(self.quiz_prompt_label)

        self.quiz_buttons = []
        for i in range(4):
            btn = QPushButton()
            btn.setStyleSheet("text-align: left; padding: 8px;")
            btn.clicked.connect(lambda _, idx=i: self._on_quiz_answer(idx))
            quiz_layout.addWidget(btn)
            self.quiz_buttons.append(btn)

        self.quiz_frame.setVisible(False)
        layout.addWidget(self.quiz_frame)

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
        for i in range(4):
            QShortcut(QKeySequence(str(i + 1)), self,
                      lambda idx=i: self._on_quiz_answer(idx))

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    # ------------------------------------------------------------------ quiz

    def show_quiz(self, question: dict, callback):
        self._quiz_question = question
        self._quiz_callback = callback
        self._quiz_answered = False
        self._auto_shown = not self.isVisible()

        self.quiz_prompt_label.setText(question["prompt"])
        for i, (btn, opt) in enumerate(zip(self.quiz_buttons, question["options"])):
            btn.setText(f"{i + 1}. {opt}")
            btn.setStyleSheet("text-align: left; padding: 8px;")
            btn.setEnabled(True)

        self.quiz_frame.setVisible(True)
        self.config_frame.setVisible(False)
        self.adjustSize()

        if self._auto_shown:
            self.show()
        self.raise_()
        self.activateWindow()

    def _on_quiz_answer(self, selected_idx: int):
        if not self.quiz_frame.isVisible() or self._quiz_answered:
            return
        self._quiz_answered = True
        correct_idx = self._quiz_question["correct_index"]
        is_correct = (selected_idx == correct_idx)

        self.quiz_buttons[correct_idx].setStyleSheet(
            "background-color: #4CAF50; color: white; text-align: left; padding: 8px;"
        )
        if not is_correct:
            self.quiz_buttons[selected_idx].setStyleSheet(
                "background-color: #F44336; color: white; text-align: left; padding: 8px;"
            )

        QTimer.singleShot(600, lambda: self._dismiss_quiz(is_correct))

    def _dismiss_quiz(self, result: bool):
        self.quiz_frame.setVisible(False)
        self.config_frame.setVisible(True)
        self.adjustSize()
        cb = self._quiz_callback
        self._quiz_callback = None
        if self._auto_shown:
            self.hide()
        if cb:
            cb(result)

    # ------------------------------------------------------------------ config controls

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

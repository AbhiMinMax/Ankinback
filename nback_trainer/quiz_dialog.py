from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut


class QuizDialog(QDialog):
    def __init__(self, question: dict, parent=None):
        super().__init__(parent)
        self.question = question
        self.answered = False
        self.result: bool | None = None
        self._setup_ui()
        self.setWindowTitle("Working Memory Check")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(420)

    def _setup_ui(self):
        layout = QVBoxLayout()

        prompt = QLabel(self.question["prompt"])
        prompt.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        prompt.setWordWrap(True)
        layout.addWidget(prompt)

        self.buttons = []
        for i, option in enumerate(self.question["options"]):
            btn = QPushButton(f"{i + 1}. {option}")
            btn.setStyleSheet("text-align: left; padding: 8px;")
            btn.setProperty("default_style", "text-align: left; padding: 8px;")
            btn.clicked.connect(lambda _, idx=i: self._on_answer(idx))
            layout.addWidget(btn)
            self.buttons.append(btn)

            sc = QShortcut(QKeySequence(str(i + 1)), self)
            sc.activated.connect(lambda idx=i: self._on_answer(idx))

        self.setLayout(layout)

    def _on_answer(self, selected_idx: int):
        if self.answered:
            return
        self.answered = True
        correct_idx = self.question["correct_index"]
        self.result = (selected_idx == correct_idx)

        self.buttons[correct_idx].setStyleSheet(
            "background-color: #4CAF50; color: white; text-align: left; padding: 8px;"
        )
        if not self.result:
            self.buttons[selected_idx].setStyleSheet(
                "background-color: #F44336; color: white; text-align: left; padding: 8px;"
            )

        QTimer.singleShot(600, self.accept)

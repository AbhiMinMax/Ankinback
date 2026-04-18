from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt


class HistoryWindow(QDialog):
    def __init__(self, session_log, parent=None):
        super().__init__(parent)
        self.session_log = session_log
        self._setup_ui()
        self.setWindowTitle("WM Trainer — Session History")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(640, 400)

    def _setup_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Time", "Deck", "N", "Score", "Accuracy %"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        for col in (0, 1, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)

        self.setLayout(layout)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def refresh(self):
        records = self.session_log.get_all()
        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(rec.get("date", "")))
            self.table.setItem(row, 1, QTableWidgetItem(rec.get("time", "")))
            deck_name = rec.get("deck", "")
            deck_item = QTableWidgetItem(deck_name)
            deck_item.setToolTip(deck_name)
            self.table.setItem(row, 2, deck_item)
            self.table.setItem(row, 3, QTableWidgetItem(str(rec.get("span_n", ""))))
            score = f"{rec.get('correct', 0)} / {rec.get('total', 0)}"
            self.table.setItem(row, 4, QTableWidgetItem(score))
            accuracy = rec.get("accuracy", 0)
            self.table.setItem(row, 5, QTableWidgetItem(f"{accuracy * 100:.1f}%"))

    def _on_clear(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Delete all session history? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.session_log.clear()
            self.refresh()

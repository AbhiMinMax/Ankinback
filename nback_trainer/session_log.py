import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionLog:
    def __init__(self, path: str):
        self.path = path
        self._records: list[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self._records = json.load(f)
            except Exception as e:
                logger.error("SessionLog._load failed to read %s: %s", self.path, e)
                self._records = []

    def save(self):
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self._records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("SessionLog.save failed to write %s: %s", self.path, e)

    def add_session(self, n: int, correct: int, total: int, deck: str, session_type: str):
        now = datetime.now()
        accuracy = round(correct / total, 3) if total > 0 else 0.0
        self._records.insert(0, {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "span_n": n,
            "correct": correct,
            "total": total,
            "accuracy": accuracy,
            "session_type": session_type,
            "deck": deck,
        })
        self.save()

    def get_all(self) -> list[dict]:
        return self._records

    def clear(self):
        self._records = []
        self.save()

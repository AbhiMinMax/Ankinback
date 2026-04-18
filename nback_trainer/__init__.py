import os
import logging

from aqt import mw, gui_hooks
from aqt.qt import QAction

from .tracker import SessionTracker
from .quiz import QuizEngine
from .popup import MainPopup
from .quiz_dialog import QuizDialog
from .history_window import HistoryWindow
from .session_log import SessionLog

logger = logging.getLogger(__name__)

tracker = SessionTracker()
quiz_engine = QuizEngine(tracker)

log_path = os.path.join(os.path.dirname(__file__), 'session_history.json')
session_log = SessionLog(log_path)

popup: MainPopup | None = None
history_win: HistoryWindow | None = None
_current_deck: str = ""


def get_popup() -> MainPopup:
    global popup
    if popup is None:
        popup = MainPopup(tracker, quiz_engine, session_log, parent=mw)
        popup.set_manual_quiz_callback(fire_quiz)
    return popup


def fire_quiz():
    p = get_popup()
    n = p.get_n()
    question = quiz_engine.generate(n)
    if question is None:
        return
    dlg = QuizDialog(question, parent=mw)
    dlg.exec()
    if dlg.result is not None:
        p.record_answer(dlg.result)


def on_show_question(card):
    global _current_deck
    try:
        _current_deck = card.col.decks.name(card.did)
        tracker.add(card)
        p = get_popup()
        if p.is_auto_mode():
            fire_quiz()
        if p.isVisible():
            p.refresh()
    except Exception as e:
        logger.error("on_show_question error: %s", e)


def on_reviewer_end():
    try:
        p = get_popup()
        cfg = mw.addonManager.getConfig(__name__) or {}
        session_type = cfg.get("session_boundary", "deck")
        total = p._session_total
        if total > 0:
            session_log.add_session(
                n=p.get_n(),
                correct=p._session_correct,
                total=total,
                deck=_current_deck,
                session_type=session_type,
            )
    except Exception as e:
        logger.error("on_reviewer_end error: %s", e)


def open_popup():
    p = get_popup()
    p.show()
    p.raise_()


def open_history():
    global history_win
    if history_win is None:
        history_win = HistoryWindow(session_log, parent=mw)
    history_win.refresh()
    history_win.show()
    history_win.raise_()


gui_hooks.reviewer_did_show_question.append(on_show_question)
gui_hooks.reviewer_will_end.append(on_reviewer_end)

action_popup = QAction("WM Trainer", mw)
action_popup.triggered.connect(open_popup)
mw.form.menuTools.addAction(action_popup)

action_history = QAction("WM Trainer — Session History", mw)
action_history.triggered.connect(open_history)
mw.form.menuTools.addAction(action_history)

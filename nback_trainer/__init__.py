import os
import json as _json
import logging

from aqt import mw, gui_hooks
from aqt.qt import QAction, QTimer

from .tracker import SessionTracker
from .quiz import QuizEngine
from .popup import MainPopup
from .history_window import HistoryWindow
from .session_log import SessionLog

logger = logging.getLogger(__name__)

tracker = SessionTracker()
quiz_engine = QuizEngine(tracker)

log_path = os.path.join(os.path.dirname(__file__), 'session_history.json')
session_log = SessionLog(log_path)

popup: MainPopup | None = None
history_win: HistoryWindow | None = None
_session_decks: set[str] = set()
_quiz_active: bool = False


def _session_deck_label() -> str:
    if not _session_decks:
        return ""
    parts_list = [d.split("::") for d in _session_decks]
    common = parts_list[0]
    for parts in parts_list[1:]:
        common = [a for a, b in zip(common, parts) if a == b]
    return "::".join(common) if common else "Multiple decks"


def get_popup() -> MainPopup:
    global popup
    if popup is None:
        popup = MainPopup(tracker, quiz_engine, session_log, parent=mw)
        popup.set_manual_quiz_callback(fire_quiz)
        _load_config(popup)
        popup.n_spin.valueChanged.connect(lambda _: _save_config())
        popup.mode_combo.currentTextChanged.connect(lambda _: _save_config())
    return popup


def _load_config(p: MainPopup):
    try:
        cfg = mw.addonManager.getConfig(__name__) or {}
        p.n_spin.setValue(cfg.get("span_n", 5))
        mode_text = "Auto" if cfg.get("quiz_mode", "auto") == "auto" else "Manual"
        p.mode_combo.setCurrentText(mode_text)
    except Exception as e:
        logger.error("_load_config error: %s", e)


def _save_config():
    try:
        p = get_popup()
        cfg = mw.addonManager.getConfig(__name__) or {}
        cfg["span_n"] = p.get_n()
        cfg["quiz_mode"] = "auto" if p.is_auto_mode() else "manual"
        mw.addonManager.writeConfig(__name__, cfg)
    except Exception as e:
        logger.error("_save_config error: %s", e)


def fire_quiz():
    global _quiz_active
    if _quiz_active:
        return
    if not mw.reviewer:
        return
    p = get_popup()
    n = p.get_n()
    question = quiz_engine.generate(n)
    if question is None:
        return
    _quiz_active = True
    QTimer.singleShot(150, lambda: _show_quiz_overlay(question))


def _show_quiz_overlay(question: dict):
    global _quiz_active
    opts_json = _json.dumps([str(o) for o in question["options"]])
    correct_idx = int(question["correct_index"])
    k = int(question["k"])

    js = f"""
(function() {{
    var old = document.getElementById('nback-overlay');
    if (old) old.remove();

    var overlay = document.createElement('div');
    overlay.id = 'nback-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;'
        + 'background:rgba(0,0,0,0.82);z-index:99999;display:flex;'
        + 'align-items:center;justify-content:center;';

    var box = document.createElement('div');
    box.style.cssText = 'background:#fff;border-radius:10px;padding:28px 32px;'
        + 'max-width:520px;width:92%;box-shadow:0 4px 32px rgba(0,0,0,0.4);';

    var title = document.createElement('div');
    title.style.cssText = 'font-size:17px;font-weight:700;margin-bottom:18px;color:#222;';
    title.textContent = 'What was card {k}-back?';
    box.appendChild(title);

    var opts = {opts_json};
    var correctIdx = {correct_idx};
    var answered = false;
    var btns = [];

    function selectAnswer(idx) {{
        if (answered) return;
        answered = true;
        document.removeEventListener('keydown', keyHandler, true);
        btns[correctIdx].style.background = '#4CAF50';
        btns[correctIdx].style.color = '#fff';
        if (idx !== correctIdx) {{
            btns[idx].style.background = '#F44336';
            btns[idx].style.color = '#fff';
        }}
        setTimeout(function() {{
            overlay.remove();
            if (typeof pycmd !== 'undefined') {{
                pycmd('nback_answer:' + idx + ':' + correctIdx);
            }}
        }}, 600);
    }}

    opts.forEach(function(opt, i) {{
        var btn = document.createElement('button');
        btn.style.cssText = 'display:block;width:100%;text-align:left;padding:10px 14px;'
            + 'margin-bottom:10px;font-size:14px;border:1px solid #ddd;border-radius:6px;'
            + 'cursor:pointer;background:#fafafa;color:#222;box-sizing:border-box;';
        btn.textContent = (i + 1) + '. ' + opt;
        btn.onmouseover = function() {{ if (!answered) this.style.background = '#f0f0f0'; }};
        btn.onmouseout  = function() {{ if (!answered) this.style.background = '#fafafa'; }};
        btn.onclick = (function(i) {{ return function() {{ selectAnswer(i); }}; }})(i);
        box.appendChild(btn);
        btns.push(btn);
    }});

    overlay.appendChild(box);
    document.body.appendChild(overlay);

    function keyHandler(e) {{
        if (!e.altKey) return;
        var n = parseInt(e.key, 10);
        if (n >= 1 && n <= 4) {{
            e.preventDefault();
            e.stopImmediatePropagation();
            selectAnswer(n - 1);
        }}
    }}
    document.addEventListener('keydown', keyHandler, true);
}})();
"""
    try:
        mw.reviewer.web.eval(js)
    except Exception as e:
        logger.error("_show_quiz_overlay error: %s", e)
        _quiz_active = False


def _on_quiz_done(result: bool):
    global _quiz_active
    _quiz_active = False
    p = get_popup()
    p.record_answer(result)
    if p.isVisible():
        p.refresh()


def on_js_message(handled, message, context):
    global _quiz_active
    if isinstance(message, str) and message.startswith("nback_answer:"):
        try:
            parts = message.split(":")
            selected = int(parts[1])
            correct_idx = int(parts[2])
            _on_quiz_done(selected == correct_idx)
        except Exception as e:
            logger.error("on_js_message error: %s", e)
            _quiz_active = False
        return (True, None)
    return handled


def on_show_question(card):
    global _session_decks, _quiz_active
    try:
        _quiz_active = False
        _session_decks.add(card.col.decks.name(card.did))
        tracker.add(card)
        p = get_popup()
        if p.is_auto_mode():
            fire_quiz()
        if p.isVisible():
            p.refresh()
    except Exception as e:
        logger.error("on_show_question error: %s", e)


def on_reviewer_end():
    global _quiz_active, _session_decks
    _quiz_active = False
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
                deck=_session_deck_label(),
                session_type=session_type,
            )
        p._session_correct = 0
        p._session_total = 0
        p._update_score()
        _session_decks = set()
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
gui_hooks.profile_will_close.append(on_reviewer_end)
gui_hooks.webview_did_receive_js_message.append(on_js_message)

action_popup = QAction("WM Trainer", mw)
action_popup.triggered.connect(open_popup)
mw.form.menuTools.addAction(action_popup)

action_history = QAction("WM Trainer — Session History", mw)
action_history.triggered.connect(open_history)
mw.form.menuTools.addAction(action_history)

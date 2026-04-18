# Anki Verbal Working Memory Trainer — Plugin Specification, Technical Guide & Development Plan

---

## 1. Purpose & Design Philosophy

This plugin turns Anki into a **verbal working memory trainer** by layering a continuous n-back recall task on top of a normal Anki review session. The user reviews cards as usual, but the plugin simultaneously drills them on *which cards they just saw*, using their actual Anki content as the stimulus.

This solves two problems with existing approaches:
- Standard n-back tasks (dual n-back, etc.) train working memory on abstract or artificial stimuli — digits, shapes, positions. Transfer to verbal/semantic memory is limited.
- Building a custom word-span app trains on irrelevant content disconnected from what the user is actually studying.

By using the user's own Anki card fronts as the n-back stimuli, working memory training and content learning reinforce each other in the same session.

---

## 2. Functional Specification

### 2.1 Core Mechanic

Every time a new card front loads in Anki's reviewer:

1. The card front is added to the session history buffer.
2. The quiz prompt fires **immediately** — before the user sees the answer — either automatically or on manual trigger (user-configured).
3. The quiz asks: *"What was the card you saw [K] steps ago?"* where K is a random integer between 1 and N (inclusive).
4. Four answer options are displayed — one correct, three distractors (see Section 2.4).
5. The user selects an answer using mouse or keyboard shortcut.
6. The app evaluates the answer immediately and updates the session score.
7. The user then engages with the Anki card normally.

### 2.2 Session History Buffer

- Stores the **front text** of every card shown during the current session, in order.
- **Duplicates are preserved** — if a card appears 3 times, it occupies 3 slots.
- Plain text only — HTML stripped before storage.
- Card fronts truncated to **100 characters** with trailing `…` for display in quiz options.
- Internal buffer capped at **10,000 entries** as a memory safety ceiling (far beyond any real session).
- Buffer is **session-scoped** — resets on Anki close or new session start (see Section 2.6 for session boundary).

### 2.3 N Parameter

- N is the **working memory span** being trained — the user must mentally maintain the last N card fronts at all times.
- When the quiz fires, it picks a random target position K between 1 and N (1-back = most recent, N-back = oldest in the window).
- The user cannot predict which position will be tested, so they must hold all N slots mentally.
- N is set via a spinbox in the popup. Range: 1–20. Default: 5.
- N can be changed mid-session; the buffer is not cleared when N changes.

### 2.4 Distractor Strategy

Given a quiz targeting position K-back:

| Option | Source |
|---|---|
| **Correct** | Card at exactly K-back in history |
| **Sibling distractor** | Card at (K−1)-back or (K+1)-back — adjacent in sequence |
| **Cousin distractor** | Card at (K−2)-back or (K+2)-back — near-adjacent in sequence |
| **Random distractor** | Any other card from recent session history outside the above slots |

This forces **precise temporal ordering** — the user cannot rely on vague familiarity ("I saw this recently") and must recall the exact position in the sequence. The difficulty scales with N naturally.

**Edge case — insufficient history:** Early in a session when the buffer has fewer entries than needed to populate all distractor slots, fall back to random recent cards to fill the remaining slots. Minimum buffer depth to show a quiz: N+2 cards (to have enough distinct options). Before that threshold is reached, the quiz does not fire.

### 2.5 Quiz Prompt UI

A modal-ish dialog that appears over or beside the Anki reviewer:

- Title: *"What was card [K]-back?"*
- Four answer buttons arranged vertically, each showing truncated card front text (max 100 chars)
- Options are shuffled randomly each time
- Keyboard shortcuts: `1`, `2`, `3`, `4` to select options
- After selection: correct answer highlighted green, selected wrong answer highlighted red (if wrong), with a 600ms display before auto-dismissal
- No manual dismiss needed — the quiz clears itself after answer + brief feedback

### 2.6 Session Boundary

Configurable via plugin settings. Options:

- **Deck review** (default): A session starts when the user opens a deck for review and ends when the review session ends (Anki's `reviewer_will_end` hook).
- **Manual**: User starts and ends sessions explicitly via buttons in the popup or Tools menu.

At session end, the session result is written to the history log (see Section 2.8).

### 2.7 Popup Window

Always-on-top, non-modal, resizable window launched from **Tools → Verbal WM Trainer**.

| Element | Description |
|---|---|
| **N spinbox** | Label: "Span (N)". Range 1–20. Default 5. |
| **Quiz mode toggle** | "Auto" (quiz fires on every card) vs "Manual" (user triggers quiz) |
| **Trigger quiz button** | Visible in Manual mode only. Shortcut: `Shift+Q` |
| **Show / Hide history button** | Toggles the last-N card list. Shortcut: `Shift+S` |
| **Clear session button** | Clears buffer and resets session score. Shortcut: `Shift+C` |
| **Session score display** | e.g. "Session: 7 / 10 (70%)" — updates live |
| **Card history list** | Scrollable read-only list of last N card fronts, newest first. Hidden by default. |

Window defaults: **360 × 200px** collapsed, **360 × 460px** expanded (history visible). `WindowStaysOnTopHint` set.

### 2.8 Session History Log

Persisted to disk as a JSON file inside the add-on folder:

```
nback_tracker/session_history.json
```

Each session record:

```json
{
  "date": "2026-04-18",
  "time": "09:32",
  "span_n": 5,
  "correct": 14,
  "total": 18,
  "accuracy": 0.778,
  "session_type": "deck",
  "deck": "Japanese Vocabulary"
}
```

**Session History Window** — launched from **Tools → WM Trainer History**:
- Separate QDialog window
- Table view: Date, Time, Deck, N, Score, Accuracy %
- Sorted newest first
- No editing — read only
- A "Clear History" button at the bottom

---

## 3. Technical Specification

### 3.1 Environment

| Property | Value |
|---|---|
| Platform | Windows 10 / 11 |
| Anki version target | 23.x and 24.x (Qt6 builds) |
| Python version | 3.9+ (bundled with Anki) |
| GUI framework | PyQt6 (bundled with Anki 23+) |
| Persistence | session_history.json + config via Anki's addonManager |

### 3.2 Add-on File Structure

```
nback_trainer/
├── __init__.py              # Entry point — hooks, menu items, wiring
├── tracker.py               # SessionTracker — in-memory history buffer
├── quiz.py                  # QuizEngine — distractor logic, question generation
├── popup.py                 # MainPopup — always-on-top control panel
├── quiz_dialog.py           # QuizDialog — the per-card MCQ prompt
├── history_window.py        # HistoryWindow — session log viewer
├── session_log.py           # SessionLog — disk persistence for session records
├── utils.py                 # strip_html(), truncate(), shortcut helpers
├── manifest.json            # Anki add-on metadata
├── config.json              # Default user config
└── session_history.json     # Auto-created on first session end (gitignored)
```

Install path:
```
%APPDATA%\Anki2\addons21\nback_trainer\
```

### 3.3 Anki Hooks Used

```python
from aqt import gui_hooks

# Fires when card front is shown — primary trigger
gui_hooks.reviewer_did_show_question.append(on_show_question)

# Fires when review session ends — used to close session and write log
gui_hooks.reviewer_will_end.append(on_reviewer_end)

# Fires when reviewer shows answer — not used, but available
# gui_hooks.reviewer_did_show_answer
```

### 3.4 tracker.py — SessionTracker

```python
class SessionTracker:
    MAX_HISTORY = 10_000

    def __init__(self):
        self._history: list[str] = []   # cleaned, truncated card fronts
        self._raw_count: int = 0        # total cards seen (including before quiz threshold)

    def add(self, card) -> None:
        """Extract front text, strip HTML, truncate, append."""
        text = card.note().fields[0]
        text = strip_html(text)
        text = strip_cloze(text)
        text = truncate(text, 100)
        self._history.append(text)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)
        self._raw_count += 1

    def get_last_n(self, n: int) -> list[str]:
        """Return last n entries, newest first."""
        return list(reversed(self._history[-n:]))

    def get_at(self, k_back: int) -> str | None:
        """Return card at k-back position (1 = most recent)."""
        idx = len(self._history) - k_back
        return self._history[idx] if idx >= 0 else None

    def get_recent(self, count: int) -> list[str]:
        """Return last `count` entries for distractor pool."""
        return self._history[-count:]

    def depth(self) -> int:
        return len(self._history)

    def clear(self) -> None:
        self._history.clear()
        self._raw_count = 0
```

### 3.5 utils.py

```python
import re
from html.parser import HTMLParser

class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
    def handle_data(self, data):
        self.text_parts.append(data)
    def get_text(self):
        return ''.join(self.text_parts).strip()

def strip_html(text: str) -> str:
    s = _HTMLStripper()
    s.feed(text)
    return s.get_text()

def strip_cloze(text: str) -> str:
    # Remove {{c1::answer}} cloze markers, keep the answer text
    text = re.sub(r'\{\{c\d+::(.*?)(?:::.*)?\}\}', r'\1', text)
    return text.strip()

def truncate(text: str, limit: int = 100) -> str:
    return text if len(text) <= limit else text[:limit] + '…'
```

### 3.6 quiz.py — QuizEngine

```python
import random

class QuizEngine:
    def __init__(self, tracker: SessionTracker):
        self.tracker = tracker

    def can_quiz(self, n: int) -> bool:
        """Need at least n+2 cards to form a valid question."""
        return self.tracker.depth() >= n + 2

    def generate(self, n: int) -> dict | None:
        """
        Returns a question dict:
        {
            "prompt": "What was card 3-back?",
            "k": 3,
            "correct": "card text",
            "options": ["opt1", "opt2", "opt3", "opt4"],  # shuffled
            "correct_index": 2  # position of correct in options
        }
        """
        if not self.can_quiz(n):
            return None

        k = random.randint(1, n)
        correct = self.tracker.get_at(k)
        if correct is None:
            return None

        distractors = self._build_distractors(k, correct)
        options = [correct] + distractors
        random.shuffle(options)

        return {
            "prompt": f"What was card {k}-back?",
            "k": k,
            "correct": correct,
            "options": options,
            "correct_index": options.index(correct)
        }

    def _build_distractors(self, k: int, correct: str) -> list[str]:
        used = {correct}
        distractors = []

        # Sibling: k-1 or k+1
        for offset in [-1, 1]:
            candidate = self.tracker.get_at(k + offset)
            if candidate and candidate not in used:
                distractors.append(candidate)
                used.add(candidate)
                break

        # Cousin: k-2 or k+2
        for offset in [-2, 2]:
            candidate = self.tracker.get_at(k + offset)
            if candidate and candidate not in used:
                distractors.append(candidate)
                used.add(candidate)
                break

        # Fill remaining slots from recent history
        pool = self.tracker.get_recent(20)
        random.shuffle(pool)
        for candidate in pool:
            if len(distractors) >= 3:
                break
            if candidate not in used:
                distractors.append(candidate)
                used.add(candidate)

        return distractors[:3]
```

### 3.7 quiz_dialog.py — QuizDialog

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
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
        layout.addWidget(prompt)

        self.buttons = []
        for i, option in enumerate(self.question["options"]):
            btn = QPushButton(f"{i+1}. {option}")
            btn.setStyleSheet("text-align: left; padding: 8px;")
            btn.clicked.connect(lambda _, idx=i: self._on_answer(idx))
            layout.addWidget(btn)
            self.buttons.append(btn)

            # Keyboard shortcuts 1–4
            sc = QShortcut(QKeySequence(str(i + 1)), self)
            sc.activated.connect(lambda idx=i: self._on_answer(idx))

        self.setLayout(layout)

    def _on_answer(self, selected_idx: int):
        if self.answered:
            return
        self.answered = True
        correct_idx = self.question["correct_index"]
        self.result = (selected_idx == correct_idx)

        # Visual feedback
        self.buttons[correct_idx].setStyleSheet(
            "background-color: #4CAF50; color: white; text-align: left; padding: 8px;"
        )
        if not self.result:
            self.buttons[selected_idx].setStyleSheet(
                "background-color: #F44336; color: white; text-align: left; padding: 8px;"
            )

        # Auto-dismiss after 600ms
        QTimer.singleShot(600, self.accept)
```

### 3.8 session_log.py — SessionLog

```python
import json
import os
from datetime import datetime

class SessionLog:
    def __init__(self, path: str):
        self.path = path
        self._records: list[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                self._records = json.load(f)

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self._records, f, indent=2, ensure_ascii=False)

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
            "deck": deck
        })
        self.save()

    def get_all(self) -> list[dict]:
        return self._records

    def clear(self):
        self._records = []
        self.save()
```

### 3.9 popup.py — MainPopup

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QTextEdit, QComboBox
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
        self._setup_ui()
        self._setup_shortcuts()
        self.setWindowTitle("WM Trainer")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Row 1: N control + quiz mode
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

        # Row 2: action buttons
        row2 = QHBoxLayout()
        self.trigger_btn = QPushButton("Quiz [Shift+Q]")
        self.trigger_btn.setVisible(False)
        self.show_btn = QPushButton("Show [Shift+S]")
        self.clear_btn = QPushButton("Clear [Shift+C]")
        row2.addWidget(self.trigger_btn)
        row2.addWidget(self.show_btn)
        row2.addWidget(self.clear_btn)
        layout.addLayout(row2)

        # Score display
        self.score_label = QLabel("Session: 0 / 0")
        self.score_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.score_label)

        # Card history list
        self.list_area = QTextEdit()
        self.list_area.setReadOnly(True)
        self.list_area.setVisible(False)
        self.list_area.setMinimumHeight(200)
        layout.addWidget(self.list_area)

        self.setLayout(layout)

        # Connections
        self.show_btn.clicked.connect(self._on_toggle_show)
        self.clear_btn.clicked.connect(self._on_clear)
        self.trigger_btn.clicked.connect(self._on_manual_quiz)
        self.mode_combo.currentTextChanged.connect(self._on_mode_change)
        self.n_spin.valueChanged.connect(self.refresh)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Shift+S"), self, self._on_toggle_show)
        QShortcut(QKeySequence("Shift+C"), self, self._on_clear)
        QShortcut(QKeySequence("Shift+Q"), self, self._on_manual_quiz)

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
        # Trigger quiz externally — see __init__.py
        pass

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
        pct = f" ({int(correct/total*100)}%)" if total > 0 else ""
        self.score_label.setText(f"Session: {correct} / {total}{pct}")

    def refresh(self):
        if self._list_visible:
            entries = self.tracker.get_last_n(self.get_n())
            self.list_area.setPlainText('\n'.join(
                f"{i+1}. {e}" for i, e in enumerate(entries)
            ))
```

### 3.10 __init__.py — Entry Point

```python
from aqt import mw, gui_hooks
from aqt.qt import QAction
import os

from .tracker import SessionTracker
from .quiz import QuizEngine
from .popup import MainPopup
from .quiz_dialog import QuizDialog
from .history_window import HistoryWindow
from .session_log import SessionLog

# Globals
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
    _current_deck = card.col.decks.name(card.did)
    tracker.add(card)
    p = get_popup()
    if p.is_auto_mode():
        fire_quiz()
    if p.isVisible():
        p.refresh()

def on_reviewer_end():
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
            session_type=session_type
        )

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

# Hooks
gui_hooks.reviewer_did_show_question.append(on_show_question)
gui_hooks.reviewer_will_end.append(on_reviewer_end)

# Menu items
action_popup = QAction("WM Trainer", mw)
action_popup.triggered.connect(open_popup)
mw.form.menuTools.addAction(action_popup)

action_history = QAction("WM Trainer — Session History", mw)
action_history.triggered.connect(open_history)
mw.form.menuTools.addAction(action_history)
```

### 3.11 config.json

```json
{
    "span_n": 5,
    "quiz_mode": "auto",
    "session_boundary": "deck"
}
```

Read via `mw.addonManager.getConfig(__name__)`. Written back on changes via `mw.addonManager.writeConfig(__name__, config)`.

### 3.12 manifest.json

```json
{
    "name": "Verbal Working Memory Trainer",
    "package": "nback_trainer",
    "author": "",
    "version": "1.0.0",
    "ankiweb_id": "",
    "homepage": "",
    "tags": ["working memory", "n-back", "trainer"],
    "conflicts": [],
    "min_point_version": 231000
}
```

---

## 4. Development Plan

### Phase 1 — Hook Verification & Text Extraction

**Goal:** Confirm core data capture works before any UI is built.

Tasks:
1. Create add-on folder, write minimal `__init__.py`
2. Implement `utils.py` — `strip_html()`, `strip_cloze()`, `truncate()`
3. Register `reviewer_did_show_question` hook, print extracted text to Anki debug console
4. Review 5–10 cards (including cloze cards and HTML-heavy cards)
5. Verify: text is clean, cloze markers removed, truncation works, no crashes

Deliverable: Verified text extraction pipeline.

---

### Phase 2 — SessionTracker

**Goal:** Reliable in-memory history buffer.

Tasks:
1. Implement `tracker.py` — `add()`, `get_at()`, `get_last_n()`, `get_recent()`, `clear()`
2. Write standalone test script (no Anki needed):
   - Populate 20 fake entries
   - Assert `get_at(1)` returns most recent
   - Assert `get_last_n(5)` returns 5 newest reversed
   - Assert `get_at(k)` returns correct historical position
   - Assert clear resets depth to 0
3. Test edge cases: k > depth (should return None), N > depth

Deliverable: `tracker.py` with passing tests.

---

### Phase 3 — QuizEngine & Distractors

**Goal:** Correct question generation with quality distractors.

Tasks:
1. Implement `quiz.py` — `generate()`, `_build_distractors()`
2. Standalone test:
   - Populate tracker with 15 distinct entries
   - Generate 20 questions, assert correct answer always present in options
   - Assert sibling distractor is adjacent in sequence when available
   - Assert options always contain exactly 4 items (no duplicates)
3. Test edge case: buffer depth exactly N+2 (minimum viable)
4. Test edge case: all recent cards are identical text — fallback gracefully

Deliverable: `quiz.py` generating valid questions reliably.

---

### Phase 4 — Quiz Dialog

**Goal:** MCQ prompt renders correctly and scores accurately.

Tasks:
1. Implement `quiz_dialog.py`
2. Test standalone with a hardcoded question dict
3. Verify: keyboard shortcuts 1–4 work, correct answer highlights green, wrong highlights red, auto-dismisses after 600ms
4. Verify: `dlg.result` is `True`/`False` correctly after exec()

Deliverable: Functional QuizDialog.

---

### Phase 5 — Main Popup Window

**Goal:** Control panel works independently.

Tasks:
1. Implement `popup.py`
2. Wire Show/Hide toggle — window resizes correctly
3. Wire Clear button — clears tracker and resets score display
4. Wire mode combo — Manual mode shows Trigger button
5. Wire N spinbox — changing N updates displayed list immediately
6. Test keyboard shortcuts `Shift+S`, `Shift+C`, `Shift+Q` while popup is focused
7. Verify score display updates correctly after `record_answer()` calls

Deliverable: Functional popup (not yet wired to live hook).

---

### Phase 6 — Full Integration

**Goal:** All components wired together in a live Anki session.

Tasks:
1. Implement `__init__.py` — wire hook → tracker → quiz fire → popup refresh
2. Test Auto mode: review 10 cards, verify quiz fires on each card front load, score increments
3. Test Manual mode: quiz only fires when Trigger button / `Shift+Q` pressed
4. Test changing N mid-session — history list updates, quiz uses new N
5. Test Clear mid-session — buffer resets, score resets, quizzes restart from scratch
6. Verify popup history list shows correct N most-recent cards

Deliverable: Fully integrated working plugin.

---

### Phase 7 — Session Log & History Window

**Goal:** Persistent session records and history viewer.

Tasks:
1. Implement `session_log.py` — `add_session()`, `get_all()`, `clear()`
2. Implement `history_window.py` — QTableWidget showing all session records
3. Wire `reviewer_will_end` hook to write session record at end of deck review
4. Test: complete a deck review, reopen Anki, verify session appears in history
5. Test: manual session boundary — start/end session manually, verify record written
6. Test: clear history — records deleted from file and table updates

Deliverable: Persistent session history working end-to-end.

---

### Phase 8 — Config Persistence & Polish

**Goal:** Release-ready build.

Tasks:
1. Load config on startup — restore last N, quiz mode, session boundary setting
2. Save config on change for all three settings
3. Handle malformed/missing config.json gracefully
4. Verify window close button hides (not destroys) the popup — reopening from Tools menu works
5. Test on Anki 23.x and 24.x
6. Test deck switching mid-session — verify deck name recorded correctly in session log
7. Cap internal buffer at 10,000 — verify oldest entries are dropped without error
8. Write README.md: installation steps, how to use, keyboard shortcuts reference

Deliverable: Final release build.

---

## 5. Key Constraints & Gotchas

| Issue | Mitigation |
|---|---|
| Anki 23+ uses PyQt6; older builds use PyQt5 | Target PyQt6 only; set `min_point_version: 231000` in manifest |
| `reviewer_did_show_question` fires on front side only | Correct hook — never use `reviewer_did_show_answer` for capture |
| Card front may contain HTML, furigana, MathJax | Strip HTML first; MathJax (`\(...\)`) can be left as-is (rare) |
| Cloze syntax survives HTML stripping | Run `strip_cloze()` as second pass after `strip_html()` |
| Quiz fires while user is still reading new card | Acceptable — this is intentional design. The interrupt is the training. |
| Early session: insufficient history for quiz | `can_quiz()` gate — no quiz fires until buffer depth ≥ N+2 |
| All distractors may be identical to correct if session has few unique cards | `used` set in `_build_distractors()` prevents duplicates; fallback to random if pool is exhausted |
| Closing popup window via X should hide, not destroy | Override `closeEvent` to call `hide()` instead of default close |
| Keyboard shortcuts only work when popup is focused | `Shift+S/C/Q` scoped to popup window; `1/2/3/4` scoped to QuizDialog |
| Session boundary = deck: need current deck name at session end | Cache `_current_deck` on each `on_show_question` call |
| Qt thread safety | All UI updates run on main thread via hooks — no threading needed |

---

## 6. File Checklist for Claude Code

```
nback_trainer/
├── __init__.py            ← hook registration, menu items, top-level wiring
├── tracker.py             ← SessionTracker
├── quiz.py                ← QuizEngine, distractor logic
├── popup.py               ← MainPopup (always-on-top control panel)
├── quiz_dialog.py         ← QuizDialog (MCQ prompt per card)
├── history_window.py      ← HistoryWindow (session log table viewer)
├── session_log.py         ← disk persistence for session records
├── utils.py               ← strip_html, strip_cloze, truncate
├── manifest.json          ← add-on metadata
├── config.json            ← default config
└── README.md              ← user-facing instructions
```

Estimated total lines of code: **500–650 lines** across all files.

---

## 7. Keyboard Shortcut Reference

| Shortcut | Action | Scope |
|---|---|---|
| `Shift+S` | Show / Hide card history list | Popup focused |
| `Shift+C` | Clear session buffer and score | Popup focused |
| `Shift+Q` | Manually trigger quiz (Manual mode) | Popup focused |
| `1` | Select option 1 | QuizDialog focused |
| `2` | Select option 2 | QuizDialog focused |
| `3` | Select option 3 | QuizDialog focused |
| `4` | Select option 4 | QuizDialog focused |

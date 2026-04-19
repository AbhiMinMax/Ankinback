# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running / Testing

There is no standalone runner or test suite. The plugin runs inside Anki. To test changes:

1. Copy `nback_trainer/` into `%APPDATA%\Anki2\addons21\nback_trainer\`
2. Restart Anki
3. Open **Tools → WM Trainer** to exercise the popup
4. Enter a review session to trigger the quiz overlay

Anki logs plugin errors to its console (Help → View Logs on Windows).

## Architecture

The plugin is a single Anki add-on package (`nback_trainer/`). Entry point is `__init__.py`, which wires everything together at import time.

**Data flow:**

```
Anki hook: reviewer_did_show_question
    → SessionTracker.add(card)       # strips HTML/cloze, appends to in-memory history list
    → QuizEngine.generate(n)         # picks random k ∈ [1,N], finds correct + 3 distractors
    → _show_quiz_overlay(question)   # injects JS into mw.reviewer.web (Anki's webview)
        → user clicks / presses 1-4
        → pycmd('nback_answer:idx:correct_idx')
    → on_js_message()                # received by webview_did_receive_js_message hook
    → MainPopup.record_answer()      # updates session score display
```

**Key design decisions:**

- The quiz is rendered as a full-screen JS overlay injected into the reviewer webview (`mw.reviewer.web.eval(js)`), not as a Qt dialog. This avoids Qt window focus/foreground issues on Windows.
- `_quiz_active` flag in `__init__.py` prevents re-entrant quiz triggers.
- `MainPopup` is a `QDialog` with `WindowStaysOnTopHint`, lazily created on first access via `get_popup()`.
- Settings (span N, quiz mode) persist via `mw.addonManager.getConfig` / `writeConfig`, backed by `config.json`.
- Session history persists to `session_history.json` in the add-on folder, written on `reviewer_will_end`.

**Module responsibilities:**

| Module | Role |
|---|---|
| `__init__.py` | Hook registration, JS bridge, config load/save, orchestration |
| `tracker.py` | In-memory ring buffer of card front-text (max 10 000) |
| `quiz.py` | Question generation — picks k, correct answer, 3 adjacent distractors |
| `popup.py` | Qt control panel (score, N spinner, mode toggle, history list) |
| `session_log.py` | JSON persistence for completed session records |
| `history_window.py` | Qt table view of past sessions |
| `utils.py` | HTML stripping, cloze unwrapping, text truncation |

## Constraints

- Qt6 only (PyQt6 imports). Do not use PyQt5 APIs.
- Anki 23.x / 24.x on Windows 10/11.
- No pip dependencies — only stdlib + Anki's bundled Qt.
- The webview JS bridge uses `pycmd(...)` → `webview_did_receive_js_message` hook. Messages must be string-prefixed (e.g. `nback_answer:`) to avoid collisions with Anki internals.

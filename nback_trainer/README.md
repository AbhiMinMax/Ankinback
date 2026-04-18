# Verbal Working Memory Trainer

An Anki add-on that layers an n-back working memory drill on top of your normal review session, using your own card fronts as stimuli.

## Installation

Copy the `nback_trainer` folder into your Anki add-ons directory:

```
%APPDATA%\Anki2\addons21\nback_trainer\
```

Restart Anki. Two new items will appear under **Tools**:
- **WM Trainer** — opens the control panel
- **WM Trainer — Session History** — opens the session log

## How It Works

Every time a card front loads during review, the plugin quizzes you: *"What was the card you saw K steps ago?"* — where K is a random integer between 1 and N. You must select the correct answer from four options (one correct, three distractors chosen from adjacent positions in sequence).

The quiz fires before you see the answer, so it interrupts the normal flow intentionally — that interrupt is the training.

## Control Panel

| Control | Description |
|---|---|
| **Span (N)** | Working memory span to train. Range 1–20, default 5. |
| **Auto / Manual** | Auto: quiz fires on every card. Manual: you trigger it. |
| **Quiz [Shift+Q]** | Manually trigger a quiz (Manual mode only). |
| **Show [Shift+S]** | Toggle the last-N card history list. |
| **Clear [Shift+C]** | Reset buffer and session score. |
| **Session score** | Live correct/total/accuracy display. |

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Shift+S` | Show / Hide card history (popup focused) |
| `Shift+C` | Clear session (popup focused) |
| `Shift+Q` | Trigger quiz manually (popup focused) |
| `1` `2` `3` `4` | Select quiz answer (quiz dialog focused) |

## Session History

Sessions are saved to `session_history.json` in the add-on folder. Open **Tools → WM Trainer — Session History** to view a table of past sessions. Records include date, time, deck, span N, score, and accuracy.

## Requirements

- Anki 23.x or 24.x (Qt6 builds)
- Windows 10 / 11

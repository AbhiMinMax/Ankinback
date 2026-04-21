from .utils import strip_html, strip_cloze, truncate


class SessionTracker:
    MAX_HISTORY = 10_000

    def __init__(self):
        self._history: list[str] = []
        self._raw_count: int = 0

    def add(self, card) -> None:
        text = card.note().fields[0]
        text = strip_html(text)
        text = strip_cloze(text)
        text = truncate(text, 100)
        self._history.append(text)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)
        self._raw_count += 1

    def get_last_n(self, n: int) -> list[str]:
        return list(reversed(self._history[-n:]))

    def get_at(self, k_back: int) -> str | None:
        # k_back=1 means the card seen immediately before the current one.
        # The current card sits at history[-1], so we subtract an extra 1.
        idx = len(self._history) - 1 - k_back
        if 0 <= idx < len(self._history):
            return self._history[idx]
        return None

    def get_recent(self, count: int) -> list[str]:
        return list(self._history[-count:])

    def depth(self) -> int:
        return len(self._history)

    def clear(self) -> None:
        self._history.clear()
        self._raw_count = 0

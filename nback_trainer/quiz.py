import random

from .tracker import SessionTracker


class QuizEngine:
    def __init__(self, tracker: SessionTracker):
        self.tracker = tracker

    def can_quiz(self, n: int) -> bool:
        return self.tracker.depth() >= n + 2

    def generate(self, n: int) -> dict | None:
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
            "correct_index": options.index(correct),
        }

    def _build_distractors(self, k: int, correct: str) -> list[str]:
        used = {correct}
        distractors = []

        for offset in [-1, 1]:
            candidate = self.tracker.get_at(k + offset)
            if candidate and candidate not in used:
                distractors.append(candidate)
                used.add(candidate)
                break

        for offset in [-2, 2]:
            candidate = self.tracker.get_at(k + offset)
            if candidate and candidate not in used:
                distractors.append(candidate)
                used.add(candidate)
                break

        pool = self.tracker.get_recent(20)
        random.shuffle(pool)
        for candidate in pool:
            if len(distractors) >= 3:
                break
            if candidate not in used:
                distractors.append(candidate)
                used.add(candidate)

        return distractors[:3]

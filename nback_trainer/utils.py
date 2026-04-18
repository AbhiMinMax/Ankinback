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
    text = re.sub(r'\{\{c\d+::(.*?)(?:::.*)?\}\}', r'\1', text)
    return text.strip()


def truncate(text: str, limit: int = 100) -> str:
    return text if len(text) <= limit else text[:limit] + '…'

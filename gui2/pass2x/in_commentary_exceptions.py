"""Exceptions list for Pass2x "in commentary".

A simple, hand-editable list of words to exclude from the candidate set
(over-eager matches such as very common particles and single letters). The
file is one word per line; the manager loads it into a set and can add to it
and save it back. Import the manager wherever the filter is needed.
"""

from pathlib import Path

DEFAULT_PATH: Path = Path("gui2/pass2x/in_commentary_exceptions.txt")


class InCommentaryExceptions:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self.path: Path = path
        self.exceptions: set[str] = set()
        self.load()

    def load(self) -> None:
        if self.path.exists():
            self.exceptions = {
                line.strip()
                for line in self.path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            "\n".join(sorted(self.exceptions)) + "\n", encoding="utf-8"
        )

    def add(self, word: str) -> None:
        self.exceptions.add(word)
        self.save()

    def __contains__(self, word: str) -> bool:
        return word in self.exceptions

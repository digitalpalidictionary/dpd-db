import csv

from tools.paths import ProjectPaths
from gui2.toolkit import ToolKit


class SandhiFileManager:
    def __init__(self, toolkit: ToolKit):
        self._pth = ProjectPaths()
        self._checked_words: set[str] = self._read_checked_csv()
        self._corrections: set[str] = self._read_corrections_csv()
        self.variants = toolkit.variants
        self.spelling_mistakes = toolkit.spelling_mistakes

    def add_variant(self, word: str, main_reading: str) -> None:
        self.variants.update_and_save(word, main_reading)

    def add_spelling_mistake(self, word: str, correct_spelling: str) -> None:
        self.spelling_mistakes.update_and_save(word, correct_spelling)

    def _read_checked_csv(self) -> set[str]:
        """Read the checked.csv file and return a set of words."""
        try:
            with open(self._pth.decon_checked, "r", newline="") as f:
                reader = csv.reader(f)
                return {row[0] for row in reader if row}
        except FileNotFoundError:
            return set()

    def _read_corrections_csv(self) -> set[str]:
        """Read the manual_corrections.tsv file and return a set of sandhi words."""
        try:
            with open(self._pth.decon_manual_corrections, "r", newline="") as f:
                reader = csv.reader(f, delimiter="\t")
                return {row[0] for row in reader if row}
        except FileNotFoundError:
            return set()

    def add_sandhi_to_checked_csv(self, word: str) -> None:
        """Add a word to the sandhi_checked.csv file, checking for duplicates."""
        # Re-read the file to ensure _checked_words is up-to-date before checking for duplicates
        self._checked_words = self._read_checked_csv()

        if word in self._checked_words:
            return

        with open(self._pth.decon_checked, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([word])
        self._checked_words.add(word)

    def update_sandhi_corrections_csv(self, sandhi_word: str, correction: str) -> None:
        """Update the sandhi_corrections.csv file, checking for duplicates."""
        # Re-read the file to ensure _corrections is up-to-date before checking for duplicates
        self._corrections = self._read_corrections_csv()

        if sandhi_word in self._corrections:
            return

        with open(self._pth.decon_manual_corrections, "a", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow([sandhi_word, correction])
        self._corrections.add(sandhi_word)

        self.add_sandhi_to_checked_csv(sandhi_word)

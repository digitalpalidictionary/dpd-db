import json
from pathlib import Path

from gui2.toolkit import ToolKit
from tools.printer import printer as pr


class Pass2EgManager:
    """Queue of missing words mined from examples and commentary at save time.

    Ticked words in the missing-words dialog are queued here with their
    sentence context, then loaded one by one with the Eg button.
    """

    def __init__(self, toolkit: ToolKit) -> None:
        self.eg_words_file_path: Path = toolkit.paths.pass2_eg_words_path
        self.eg_words_dict: dict[str, dict[str, str]] = {}
        self.load_data()

    def load_data(self) -> None:
        """Load the queue from its JSON file."""
        if self.eg_words_file_path.exists():
            try:
                with open(self.eg_words_file_path, "r", encoding="utf-8") as f:
                    self.eg_words_dict = json.load(f)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
                pr.red(f"Error loading pass2_eg_words: {e}")
                self.eg_words_dict = {}

    def save_data(self) -> None:
        """Atomic write: write to temp then replace."""
        try:
            self.eg_words_file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path: Path = self.eg_words_file_path.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.eg_words_dict, f, indent=4, ensure_ascii=False)
            tmp_path.replace(self.eg_words_file_path)
        except (OSError, TypeError, ValueError) as e:
            pr.red(f"Error saving pass2_eg_words: {e}")

    def add_word(self, word: str, prefill: dict[str, str], comment: str) -> None:
        """Add or update a word in the queue with its prefill field data."""
        entry = dict(prefill)
        entry["comment"] = comment
        self.eg_words_dict[word] = entry
        self.save_data()

    def get_next(self) -> tuple[str | None, dict[str, str] | None]:
        """Return the next queued word and delete it from the queue."""
        if self.eg_words_dict:
            word, prefill = next(iter(self.eg_words_dict.items()))
            del self.eg_words_dict[word]
            self.save_data()
            return word, prefill
        return None, None

    def is_queued(self, word: str) -> bool:
        return word in self.eg_words_dict

    def count(self) -> int:
        return len(self.eg_words_dict)

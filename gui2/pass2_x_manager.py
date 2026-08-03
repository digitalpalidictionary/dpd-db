import json
from pathlib import Path

from gui2.toolkit import ToolKit
from tools.printer import printer as pr


class Pass2XManager:
    """Queue of raw headword data to import into pass2add with the X button.

    Each entry is a dict of dpd field values keyed by lemma. An entry carrying
    an "id" updates that headword; without one it is a new word.

    !!! The X button is a scratch slot for one-off data entry. Replace the
    contents of pass2_x_words.json to change what it does — the queue file is
    gitignored and expected to be swapped out for every new batch. Nothing
    here should be pinned down by tests. !!!
    """

    def __init__(self, toolkit: ToolKit) -> None:
        self.x_words_file_path: Path = toolkit.paths.pass2_x_words_path
        self.x_words_done_path: Path = toolkit.paths.pass2_x_words_done_path
        self.x_words_dict: dict[str, dict[str, str]] = {}
        self.load_data()

    def load_data(self) -> None:
        """Load the queue from its JSON file."""
        if self.x_words_file_path.exists():
            try:
                with open(self.x_words_file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # The file is hand-authored and swapped per batch, so a bad edit
                # should be reported here rather than failing obscurely later.
                if not isinstance(loaded, dict) or any(
                    not isinstance(data, dict) for data in loaded.values()
                ):
                    raise ValueError("expected a mapping of lemma to field data")
                self.x_words_dict = loaded
            except (json.JSONDecodeError, OSError, UnicodeDecodeError, ValueError) as e:
                pr.red(f"Error loading pass2_x_words: {e}")
                self.x_words_dict = {}

    def save_data(self) -> None:
        """Atomic write: write to temp then replace."""
        try:
            self.x_words_file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path: Path = self.x_words_file_path.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.x_words_dict, f, indent=4, ensure_ascii=False)
            tmp_path.replace(self.x_words_file_path)
        except (OSError, TypeError, ValueError) as e:
            pr.red(f"Error saving pass2_x_words: {e}")

    def _archive(self, word: str, data: dict[str, str]) -> None:
        """Keep a copy of every entry taken off the queue. The queue file is
        hand-authored and gitignored, so a misclick or an abandoned entry would
        otherwise destroy the only copy of its text."""
        done: dict[str, dict[str, str]] = {}
        if self.x_words_done_path.exists():
            try:
                with open(self.x_words_done_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    done = loaded
            except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
                pr.red(f"Error loading pass2_x_words_done: {e}")
        done[word] = data
        try:
            with open(self.x_words_done_path, "w", encoding="utf-8") as f:
                json.dump(done, f, indent=4, ensure_ascii=False)
        except (OSError, TypeError, ValueError) as e:
            pr.red(f"Error saving pass2_x_words_done: {e}")

    def get_next(self) -> tuple[str | None, dict[str, str] | None]:
        """Return the next queued word and delete it from the queue.

        Reloads from disk first: the queue file is swapped out between batches
        while the app stays open, and this view is built once at warm-up.
        """
        self.load_data()
        if self.x_words_dict:
            word, data = next(iter(self.x_words_dict.items()))
            del self.x_words_dict[word]
            self.save_data()
            self._archive(word, data)
            return word, data
        return None, None

    def requeue(self, word: str, data: dict[str, str]) -> None:
        """Put an entry back after a failed load, so it is not lost."""
        self.x_words_dict[word] = data
        self.save_data()

    def remaining_count(self) -> int:
        self.load_data()
        return len(self.x_words_dict)

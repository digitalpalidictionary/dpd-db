# -*- coding: utf-8 -*-
import json

from gui2.books import SuttaCentralSegment
from gui2.paths import Gui2Paths
from tools.cst_source_sutta_example import CstSourceSuttaExample
from tools.printer import printer as pr


class Pass2PreFileManager:
    def __init__(self, book: str, paths: Gui2Paths) -> None:
        self._gui2pth: Gui2Paths = paths
        self._json_path = self._gui2pth.gui2_data_path / f"pass2_pre_{book}.json"
        self.unmatched: dict[str, list[int]] = {}
        self.matched: dict[str, dict[str, int | tuple[str, str, str]]] = {}
        self.new_word: dict[str, tuple] = {}
        self.processed: list[str] = []
        self.load_data()

    def load_data(self) -> bool:
        """Loads the manager's state from a JSON file."""

        if self._json_path.exists():
            try:
                with open(self._json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.unmatched = data.get("unmatched", {})
                    self.matched = data.get("matched", {})
                    self.new_word = data.get("new_word", {})
                    self.processed = data.get("processed", [])
                return True
            except json.JSONDecodeError as e:
                pr.red(f"Error loading pass2_pre data (invalid JSON): {e}")
                self.unmatched = {}
                self.matched = {}
                self.new_word = {}
                return False
            except Exception as e:
                pr.red(f"Unexpected error loading data: {e}")
                self.unmatched = {}
                self.matched = {}
                self.new_word = {}
                return False
        else:
            print(f"[yellow]pass2_pre data file not found at {self._json_path}")
            return False

    def save_data(self) -> None:
        """Saves the manager's current state to a JSON file."""
        try:
            self._json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "unmatched": self.unmatched,
                        "matched": self.matched,
                        "new_word": self.new_word,
                        "processed": self.processed,
                    },
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
        except IOError as e:
            pr.red(f"Error saving pass2_pre data: {e}")
        except Exception as e:
            pr.red(f"Unexpected error saving data: {e}")

    def update_unmatched(
        self,
        word_in_text: str,
        headword_id: int,
    ) -> str:
        """Adds or updates an entry in the 'unmatched' dictionary."""

        if word_in_text not in self.unmatched:
            self.unmatched[word_in_text] = []
        if headword_id not in self.unmatched[word_in_text]:
            self.unmatched[word_in_text].append(headword_id)
        self.save_data()
        message = f"Updated 'unmatched' for '{word_in_text}' with id {headword_id}"
        return message

    def update_matched(
        self,
        word_in_text: str,
        headword_id: int,
        sentence: SuttaCentralSegment | CstSourceSuttaExample,
    ) -> str:
        """Adds or updates an entry in the 'matched' dictionary."""

        self.matched[word_in_text] = {
            "id": headword_id,
            "sentence": sentence,
        }
        self.save_data()
        message = f"Updated 'matched' for '{word_in_text}' with id {headword_id}"
        return message

    def update_new_word(
        self,
        word_in_text: str,
        sentence_data: SuttaCentralSegment | CstSourceSuttaExample,
    ) -> str:
        """Adds or updates an entry in the 'new_word' dictionary."""

        self.new_word[word_in_text] = sentence_data
        self.save_data()
        message = f"Updated 'new_word' for '{word_in_text}'"
        return message

    def move_matched_item_to_processed(self, word_in_text: str) -> str:
        """
        1. Removes an entry from the 'matched' dictionary,
        2. updates the processed dictionary
        3. and saves the data.
        """

        if word_in_text in self.matched:
            self.matched.pop(word_in_text)
            self.processed.append(word_in_text)
            self.save_data()
            message = f"Moved '{word_in_text}' from 'matched' to 'processed'"
            return message
        return f"'{word_in_text}' not found in 'matched' items"

    def get_next_new_word(self):
        """Return a tuple of the next new_word item
        and delete it from the new_word dictionary."""

        if self.new_word:
            word_in_text, sentence_data = next(iter(self.new_word.items()))
            del self.new_word[word_in_text]
            self.save_data()
            return word_in_text, sentence_data
        return None, None

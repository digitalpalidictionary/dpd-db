import json
from pathlib import Path

from gui2.books import SuttaCentralSegment
from gui2.toolkit import ToolKit
from tools.cst_source_sutta_example import CstSourceSuttaExample
from tools.printer import printer as pr


class Pass2NewWordManager:
    def __init__(self, toolkit: ToolKit) -> None:
        self.new_words_file_path: Path = toolkit.paths.pass2_new_words_path
        self.new_words_dict: dict[str, dict[str, str]] = {}
        self.load_data()

    def load_data(self) -> bool:
        """Loads the manager's state from a JSON file."""

        if self.new_words_file_path.exists():
            try:
                with open(self.new_words_file_path, "r", encoding="utf-8") as f:
                    self.new_words_dict = json.load(f)

                return True
            except json.JSONDecodeError as e:
                pr.red(f"Error loading pass2 new_words (invalid JSON): {e}")
                self.new_words_dict = {}
                return False
            except Exception as e:
                pr.red(f"Unexpected error loading data: {e}")
                self.new_words_dict = {}
                return False
        else:
            return False

    def save_data(self) -> None:
        """Saves the manager's current state to a JSON file."""
        try:
            self.new_words_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.new_words_file_path, "w", encoding="utf-8") as f:
                json.dump(self.new_words_dict, f, indent=4, ensure_ascii=False)
        except IOError as e:
            pr.red(f"Error saving pass2_new_words: {e}")
        except Exception as e:
            pr.red(f"Unexpected error saving pass2_new_words: {e}")

    def update_new_word(
        self,
        word_in_text: str,
        sentence_data: SuttaCentralSegment | CstSourceSuttaExample,
    ) -> str:
        """Adds or updates an entry in the 'new_word' dictionary."""

        self.new_words_dict[word_in_text] = {
            "source": sentence_data[0],
            "sutta": sentence_data[1],
            "example": sentence_data[2],
        }

        self.save_data()
        message = f"Added {word_in_text} to new_words."
        return message

    def get_next_new_word(self):
        """Return a tuple of the next new_word item and data,
        and delete it from the new_word dictionary."""

        if self.new_words_dict:
            word_in_text, sentence_data = next(iter(self.new_words_dict.items()))
            del self.new_words_dict[word_in_text]
            self.save_data()
            return word_in_text, sentence_data
        return None, None

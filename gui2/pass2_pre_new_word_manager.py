# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Any

from gui2.books import SuttaCentralSegment
from gui2.toolkit import ToolKit
from tools.cst_source_sutta_example import CstSourceSuttaExample
from tools.printer import printer as pr


class Pass2NewWordManager:
    def __init__(self, toolkit: ToolKit) -> None:
        self.new_words_file_path: Path = toolkit.paths.pass2_new_words_path
        self.new_words_dict: dict[str, dict[str, str]] = {}
        self.load_data()
        # Ensure schema has 'comment' for all entries on load
        self._ensure_schema()

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

    def _ensure_schema(self) -> None:
        """Backfill missing 'comment' field for all entries."""
        changed: bool = False
        for key, data in list(self.new_words_dict.items()):
            if isinstance(data, dict) and "comment" not in data:
                data["comment"] = ""
                changed = True
        if changed:
            self.save_data()

    def save_data(self) -> None:
        """Saves the manager's current state to a JSON file."""
        try:
            self.new_words_file_path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write: write to temp then replace
            tmp_path: Path = self.new_words_file_path.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.new_words_dict, f, indent=4, ensure_ascii=False)
            tmp_path.replace(self.new_words_file_path)
        except IOError as e:
            pr.red(f"Error saving pass2_new_words: {e}")
        except Exception as e:
            pr.red(f"Unexpected error saving pass2_new_words: {e}")

    def update_new_word(
        self,
        word_in_text: str,
        sentence_data: SuttaCentralSegment | CstSourceSuttaExample,
        comment: str | None = None,
    ) -> str:
        """Adds or updates an entry in the 'new_word' dictionary."""
        # sentence_data is indexable as per existing usage
        self.new_words_dict[word_in_text] = {
            "source_1": sentence_data[0],
            "sutta_1": sentence_data[1],
            "example_1": sentence_data[2],
            "comment": comment or "",
        }
        self.save_data()
        message = f"Added {word_in_text} to new_words."
        return message

    def get_next_new_word(self) -> tuple[str | None, dict[str, Any] | None]:
        """Return next new_word item and delete it from the dictionary."""
        if self.new_words_dict:
            word_in_text, sentence_data = next(iter(self.new_words_dict.items()))
            # Ensure schema for the returned item
            if isinstance(sentence_data, dict) and "comment" not in sentence_data:
                sentence_data["comment"] = ""
            del self.new_words_dict[word_in_text]
            self.save_data()
            return word_in_text, sentence_data
        return None, None

import json
from pathlib import Path
from typing import Any, Dict, List

from gui2.paths import Gui2Paths
from tools.printer import printer as pr


class HistoryManager:
    """Manages a list of recently added/updated headwords."""

    def __init__(self, max_size: int = 20):
        self._gui2pth = Gui2Paths()
        self._history_path: Path = self._gui2pth.history_json_path
        self.max_size: int = max_size
        self.history: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Loads history from the JSON file."""
        if self._history_path.exists():
            try:
                with open(self._history_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # Ensure it's a list and contains dictionaries
                    if isinstance(loaded_data, list) and all(
                        isinstance(item, dict) for item in loaded_data
                    ):
                        self.history = loaded_data[: self.max_size]  # Truncate on load
                    else:
                        pr.warning(
                            f"History file format error in {self._history_path}. Starting fresh."
                        )
                        self.history = []
            except json.JSONDecodeError as e:
                pr.error(f"Error decoding history file {self._history_path}: {e}")
                self.history = []
            except Exception as e:
                pr.error(f"Unexpected error loading history: {e}")
                self.history = []
        else:
            self.history = []

    def _save(self) -> None:
        """Saves the current history to the JSON file."""
        try:
            self._history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except IOError as e:
            pr.error(f"Error saving history file {self._history_path}: {e}")
        except Exception as e:
            pr.error(f"Unexpected error saving history: {e}")

    def add_item(self, headword_id: int, lemma_1: str) -> bool:
        """Adds a new item to the beginning of the history, removes duplicates, truncates, and saves.
        Returns True if the item was not already the first item, False otherwise."""
        new_item = {"id": headword_id, "lemma_1": lemma_1}

        # Check if the item is already the first item
        was_already_first = bool(
            self.history and self.history[0].get("id") == headword_id
        )

        # Remove existing item with the same id before adding the new one at the front
        self.history = [item for item in self.history if item.get("id") != headword_id]

        self.history.insert(0, new_item)
        self.history = self.history[: self.max_size]  # Ensure max size
        self._save()
        return not was_already_first  # Return True if it wasn't the first item

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns a copy of the current history."""
        return self.history[:]

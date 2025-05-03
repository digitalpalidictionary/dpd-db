import json
import re  # Import the re module
from pathlib import Path
from typing import Dict, Optional, Tuple

from gui2.paths import Gui2Paths
from tools.printer import printer as pr


class ExampleStashManager:
    """Manages stashing and reloading example data (source, sutta, example)."""

    def __init__(self):
        self._gui2pth = Gui2Paths()
        self._stash_path: Path = self._gui2pth.example_stash_json_path
        self.stash_data: Dict[str, Dict[str, str]] = {}
        self._stash_key = "shared_stash"  # Use a fixed key for the single stash
        self._load()

    def _load(self) -> None:
        """Loads stash data from the JSON file."""
        if self._stash_path.exists():
            try:
                with open(self._stash_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # Basic validation
                    if isinstance(loaded_data, dict):
                        self.stash_data = loaded_data
                    else:
                        pr.warning(
                            f"Stash file format error in {self._stash_path}. Starting fresh."
                        )
                        self.stash_data = {}
            except json.JSONDecodeError as e:
                pr.error(f"Error decoding stash file {self._stash_path}: {e}")
                self.stash_data = {}
            except Exception as e:
                pr.error(f"Unexpected error loading stash: {e}")
                self.stash_data = {}
        else:
            self.stash_data = {}  # Initialize if file doesn't exist

    def _save(self) -> None:
        """Saves the current stash data to the JSON file."""
        try:
            self._stash_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._stash_path, "w", encoding="utf-8") as f:
                json.dump(self.stash_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            pr.error(f"Error saving stash file {self._stash_path}: {e}")
        except Exception as e:
            pr.error(f"Unexpected error saving stash: {e}")

    def stash(self, source: str, sutta: str, example: str) -> None:
        """Stashes the data into the shared slot."""
        # Remove bold tags from the example before stashing
        cleaned_example = re.sub(r"</?b>", "", example)
        self.stash_data[self._stash_key] = {
            "source": source,
            "sutta": sutta,
            "example": cleaned_example,  # Use the cleaned example
        }
        self._save()

    def reload(self) -> Optional[Tuple[str, str, str]]:
        """Reloads the shared stashed data, returning (source, sutta, example) or None."""
        data = self.stash_data.get(self._stash_key)
        if data:
            return (
                data.get("source", ""),
                data.get("sutta", ""),
                data.get("example", ""),
            )
        return None

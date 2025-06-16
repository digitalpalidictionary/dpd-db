# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path
from typing import Optional

from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit
from tools.printer import printer as pr


class ExampleStashManager:
    """Manages stashing and reloading example data (source, sutta, example)."""

    def __init__(self, toolkit: ToolKit):
        self._gui2pth: Gui2Paths = toolkit.paths
        self._stash_path: Path = self._gui2pth.example_stash_json_path
        self.stash_data: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """Load stash data from JSON file."""
        if not self._stash_path.exists():
            self.stash_data = {}
            return

        try:
            with open(self._stash_path, "r", encoding="utf-8") as f:
                if loaded := json.load(f):
                    self.stash_data = loaded if isinstance(loaded, dict) else {}
        except (json.JSONDecodeError, Exception) as e:
            pr.error(f"Error loading stash {self._stash_path}: {e}")
            self.stash_data = {}

    def _save(self) -> None:
        """Save current stash data to JSON file."""
        try:
            self._stash_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._stash_path, "w", encoding="utf-8") as f:
                json.dump(self.stash_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pr.error(f"Error saving stash {self._stash_path}: {e}")

    def stash(self, key: str, source: str, sutta: str, example: str) -> None:
        """Stash data into specified slot."""
        self.stash_data[key] = {
            "source": source,
            "sutta": sutta,
            "example": re.sub(r"</?b>", "", example),
        }
        self._save()

    def reload(self, key: str) -> Optional[tuple[str, str, str]]:
        """Reload stashed data from specified slot."""
        if data := self.stash_data.get(key):
            return (
                data.get("source", ""),
                data.get("sutta", ""),
                data.get("example", ""),
            )
        return None

    @property
    def last_example(self) -> Optional[tuple[str, str, str]]:
        """Get the last stashed example."""
        return self.reload("last")

    @last_example.setter
    def last_example(self, value: tuple[str, str, str]) -> None:
        """Set the last example."""
        source, sutta, example = value
        self.stash("last", source, sutta, example)

    def stash_shared_example(self, source: str, sutta: str, example: str) -> None:
        """Stashes the shared example data (backward compatibility)."""
        self.stash("stash", source, sutta, example)

    def reload_shared_example(self) -> Optional[tuple[str, str, str]]:
        """Reloads the shared example data (backward compatibility)."""
        return self.reload("stash")

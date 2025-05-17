import json
from pathlib import Path

from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit


class Pass2AutoFileManager:
    def __init__(
        self,
        toolkit: ToolKit,
    ):
        self.gui2pth: Gui2Paths = toolkit.paths
        self.pass2_auto_json_path: Path = self.gui2pth.pass2_auto_json_path
        self.pass2_auto_data: dict[str, dict[str, str]] = {}
        self._current_index: int = 0
        self._ensure_directory_exists()
        self.load()

    def _ensure_directory_exists(self) -> None:
        self.pass2_auto_json_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        try:
            with open(self.pass2_auto_json_path, "r", encoding="utf-8") as f:
                self.pass2_auto_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.pass2_auto_data = {}

    def save(self) -> None:
        with open(self.pass2_auto_json_path, "w", encoding="utf-8") as f:
            json.dump(self.pass2_auto_data, f, indent=4, ensure_ascii=False)

    def update_pass2_auto_data(self, headword_id: str, value: dict[str, str]) -> None:
        self.load()
        self.pass2_auto_data[headword_id] = value
        self.save()

    def delete_item(self, headword_id: str) -> bool:
        """Removes a pass2_auto item by headword_id and saves."""

        if headword_id in self.pass2_auto_data:
            del self.pass2_auto_data[headword_id]
            self.save()
            return True
        return False

    def get_pass2_auto_data(self) -> dict[str, dict[str, str]]:
        self.load()
        return self.pass2_auto_data.copy()

    def get_headword(self, headword_id: str) -> dict[str, str]:
        self.load()
        return self.pass2_auto_data.get(headword_id, {}).copy()

    def get_next_headword_data(self) -> tuple[str | None, dict[str, str]]:
        """Get the next headword data from pass2_auto.json."""
        self.load()
        headword_ids = list(self.pass2_auto_data.keys())

        if not headword_ids or self._current_index >= len(headword_ids):
            self._current_index = 0
            return (None, {})

        headword_id = headword_ids[self._current_index]
        data = self.pass2_auto_data[headword_id].copy()
        # self._current_index += 1
        return (headword_id, data)

    def reset_index(self) -> None:
        """Reset the current index to the beginning."""
        self._current_index = 0

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
        self.responses_path: Path = self.gui2pth.pass2_auto_json_path
        self.responses: dict[str, dict[str, str]] = {}
        self._current_index: int = 0
        self._ensure_directory_exists()
        self.load()

    def _ensure_directory_exists(self) -> None:
        self.responses_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        try:
            with open(self.responses_path, "r", encoding="utf-8") as f:
                self.responses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.responses = {}

    def save(self) -> None:
        with open(self.responses_path, "w", encoding="utf-8") as f:
            json.dump(self.responses, f, indent=4, ensure_ascii=False)

    def update_response(self, headword_id: str, value: dict[str, str]) -> None:
        self.responses[headword_id] = value
        self.save()

    def remove_response(self, headword_id: str) -> bool:
        """Removes a response by headword_id and saves."""
        if headword_id in self.responses:
            del self.responses[headword_id]
            self.save()
            return True
        return False

    def get_responses(self) -> dict[str, dict[str, str]]:
        return self.responses.copy()

    def get_headword(self, headword_id: str) -> dict[str, str]:
        return self.responses.get(headword_id, {}).copy()

    def get_next_headword_data(self) -> tuple[str | None, dict[str, str]]:
        """Get the next headword data from pass2_auto.json."""
        headword_ids = list(self.responses.keys())
        if not headword_ids or self._current_index >= len(headword_ids):
            self._current_index = 0
            return (None, {})

        headword_id = headword_ids[self._current_index]
        data = self.responses[headword_id].copy()
        self._current_index += 1
        return (headword_id, data)

    def reset_index(self) -> None:
        """Reset the current index to the beginning."""
        self._current_index = 0

import json
from pathlib import Path

from gui2.class_paths import Gui2Paths


class Pass2AutoFileManager:
    def __init__(self):
        self.gui2pth = Gui2Paths()
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


if __name__ == "__main__":
    # Example usage
    manager = Pass2AutoFileManager()
    print("Initial responses:", manager.get_responses())
    manager.update_response("1", {"field": "value1"})
    manager.update_response("2", {"field": "value2"})
    manager.update_response("3", {"field": "value3"})
    print("After updates:", manager.get_responses())

    print("\nGetting next entries:")
    for _ in range(5):
        headword_id, data = manager.get_next_headword_data()
        print(f"Next entry: ID={headword_id}, Data={data}")

    print("\nResetting index and getting next entries:")
    manager.reset_index()
    for _ in range(2):
        headword_id, data = manager.get_next_headword_data()
        print(f"Next entry: ID={headword_id}, Data={data}")

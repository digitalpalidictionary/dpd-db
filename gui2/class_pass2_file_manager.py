import json

from gui2.class_paths import Gui2Paths


class Pass2AutoFileManager:
    def __init__(self):
        self.gui2pth = Gui2Paths()
        self.responses_path = self.gui2pth.pass2_auto_json_path
        self.responses: dict[str, dict[str, str]] = {}
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
        """Get the next headword data from pass2_auto.json.
        Returns tuple of (headword_id, data_dict) or (None, {}) if empty."""
        if not self.responses:
            return (None, {})

        # Get first key (simplified per user request)
        headword_id = next(iter(self.responses))
        return (headword_id, self.responses[headword_id].copy())


if __name__ == "__main__":
    # Example usage
    manager = Pass2AutoFileManager()
    print("Initial responses:", manager.get_responses())
    manager.update_response("1", {"field": "value"})
    print("After update:", manager.get_responses())

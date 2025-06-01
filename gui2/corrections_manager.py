import json

from db.models import DpdHeadword


class CorrectionsManager:
    from gui2.toolkit import ToolKit

    def __init__(self, toolkit: ToolKit):
        self.paths = toolkit.paths
        self.corrections_path = self.paths.corrections_path
        self.corrections_dict: dict[str, dict[str, str | int]] = self.load_corrections()

    def load_corrections(self):
        try:
            with open(self.corrections_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_corrections(self) -> None:
        with open(self.corrections_path, "w") as f:
            json.dump(self.corrections_dict, f, ensure_ascii=False, indent=4)

    def update_corrections(self, word: DpdHeadword, comment: str):
        word_dict = word_dict = {
            k: v for k, v in vars(word).items() if not k.startswith("_")
        }
        word_dict["comment"] = comment
        self.corrections_dict[str(word.id)] = word_dict
        self.save_corrections()

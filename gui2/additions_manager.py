import json

AdditionsDict = dict[str, dict[str, str | int]]


class AdditionsManager:
    from db.models import DpdHeadword
    from gui2.toolkit import ToolKit

    def __init__(self, toolkit: ToolKit):
        self.paths = toolkit.paths
        self.additions_path = self.paths.additions_path
        self.additions_dict: AdditionsDict = self.load_additions()

    def load_additions(self) -> AdditionsDict:
        try:
            with open(self.additions_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_additions(self) -> None:
        with open(self.additions_path, "w") as f:
            json.dump(self.additions_dict, f, ensure_ascii=False, indent=4)

    def add_additions(self, word: DpdHeadword, comment: str) -> None:
        word_dict = {k: v for k, v in vars(word).items() if not k.startswith("_")}
        word_dict["comment"] = comment
        self.additions_dict[str(word.id)] = word_dict
        self.save_additions()

    def is_not_in_additions(self, id_no: int) -> bool:
        return str(id_no) not in self.additions_dict.keys()

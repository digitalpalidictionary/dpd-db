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

    def get_next_addition(self) -> tuple[dict[str, str | int] | None, int]:
        """
        Retrieves and removes the next addition from the dictionary.
        Returns a tuple of (addition, additions_remaining).
        Addition is None if no additions are available.
        """
        if not self.additions_dict:
            return None, 0

        # Get the first key (arbitrary order for now, can be improved if needed)
        first_key = next(iter(self.additions_dict))
        addition = self.additions_dict.pop(first_key)
        self.save_additions()
        return addition, len(self.additions_dict)

    def save_processed_addition(self, word_data: dict[str, str]) -> None:
        """
        Saves processed addition data to additions_added.json.
        Creates the file if it doesn't exist, or appends to existing file.

        Args:
            word_data: Dictionary containing processed word data to save
        """
        existing_data = []

        try:
            with open(self.paths.additions_added_path) as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        existing_data.append(word_data)

        with open(self.paths.additions_added_path, "w") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

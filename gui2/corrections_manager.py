# -*- coding: utf-8 -*-
import json

from db.models import DpdHeadword

CorrectionsDict = dict[str, dict[str, str | int]]


class CorrectionsManager:
    from gui2.toolkit import ToolKit

    def __init__(self, toolkit: ToolKit):
        self.paths = toolkit.paths
        self.corrections_path = self.paths.corrections_path
        self.corrections_dict: CorrectionsDict = self.load_corrections()

    def load_corrections(self) -> CorrectionsDict:
        merged: CorrectionsDict = {}

        try:
            with open(self.corrections_path) as f:
                merged = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Primary user: import all contributor corrections_*.json files
        if self.corrections_path.name == "corrections.json":
            data_dir = self.corrections_path.parent
            imported_any = False
            for contrib_file in sorted(data_dir.glob("corrections_*.json")):
                if "corrections_added" in contrib_file.name:
                    continue
                try:
                    with open(contrib_file) as f:
                        contrib_data = json.load(f)
                    if contrib_data:
                        merged.update(contrib_data)
                        contrib_file.write_text("{}")
                        imported_any = True
                except (FileNotFoundError, json.JSONDecodeError):
                    continue

            if imported_any:
                self._save_dict(merged)

        return merged

    def _save_dict(self, data: CorrectionsDict) -> None:
        with open(self.corrections_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def save_corrections(self) -> None:
        self._save_dict(self.corrections_dict)

    def update_corrections(self, word: DpdHeadword, comment: str) -> None:
        word_dict = {k: v for k, v in vars(word).items() if not k.startswith("_")}
        word_dict["comment"] = comment
        self.corrections_dict[str(word.id)] = word_dict
        self.save_corrections()

    def get_next_correction(self) -> tuple[dict[str, str | int] | None, int]:
        """
        Retrieves and removes the next correction from the dictionary.
        Returns a tuple of (correction, corrections_remaining).
        Correction is None if no corrections are available.
        """
        if not self.corrections_dict:
            return None, 0

        # Get the first key (arbitrary order for now, can be improved if needed)
        first_key = next(iter(self.corrections_dict))
        correction = self.corrections_dict.pop(first_key)
        self.save_corrections()
        return correction, len(self.corrections_dict)

    def save_processed_correction(self, word_data: dict[str, str]) -> None:
        """
        Saves processed correction data to corrections_added.json.
        Creates the file if it doesn't exist, or appends to existing file.

        Args:
            word_data: Dictionary containing processed word data to save
        """
        existing_data = []

        try:
            with open(self.paths.corrections_added_path) as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        existing_data.append(word_data)

        with open(self.paths.corrections_added_path, "w") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

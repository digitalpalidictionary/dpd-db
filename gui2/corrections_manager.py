# -*- coding: utf-8 -*-
import json
from pathlib import Path

from db.models import DpdHeadword
from tools.printer import printer as pr

CorrectionsDict = dict[str, dict[str, str | int]]


class CorrectionsManager:
    from gui2.toolkit import ToolKit

    def __init__(self, toolkit: ToolKit):
        self.paths = toolkit.paths
        self.corrections_path = self.paths.corrections_path
        self._origin: dict[str, Path] = {}
        self.corrections_dict: CorrectionsDict = self.load_corrections()

    def load_corrections(self) -> CorrectionsDict:
        """Primary user: non-destructively merge all contributor files.
        Contributor (non-primary) user: load only their own file.
        """
        merged: CorrectionsDict = {}
        self._origin = {}

        if self.corrections_path.name == "corrections.json":
            data_dir = self.corrections_path.parent
            for contrib_file in sorted(data_dir.glob("corrections_*.json")):
                if "corrections_added" in contrib_file.name:
                    continue
                try:
                    with open(contrib_file) as f:
                        contrib_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
                for key, value in contrib_data.items():
                    if key in merged:
                        pr.red(
                            f"duplicate correction key {key} in {contrib_file.name}; "
                            f"overriding previous origin {self._origin[key].name}"
                        )
                    merged[key] = value
                    self._origin[key] = contrib_file
        else:
            try:
                with open(self.corrections_path) as f:
                    merged = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

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

    def get_next_correction(
        self,
    ) -> tuple[dict[str, str | int] | None, Path | None, int]:
        """Retrieves and removes the next correction from the in-memory queue.

        Returns (correction, origin_path, corrections_remaining). For the
        primary user flow, origin_path is the contributor file the item came
        from. Correction and origin_path are None if no corrections available.
        """
        if not self.corrections_dict:
            return None, None, 0

        first_key = next(iter(self.corrections_dict))
        correction = self.corrections_dict.pop(first_key)
        origin = self._origin.pop(first_key, None)
        return correction, origin, len(self.corrections_dict)

    def save_processed_correction(
        self,
        word_data: dict[str, str],
        origin_path: Path | None = None,
    ) -> None:
        """Append processed correction to corrections_added.json, tagging the
        contributor, and remove that key from the origin contributor file.
        """
        contributor = _contributor_from_origin(origin_path, prefix="corrections_")

        existing_data: list[dict] = []
        try:
            with open(self.paths.corrections_added_path) as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        tagged = {**word_data, "_contributor": contributor}
        existing_data.append(tagged)

        with open(self.paths.corrections_added_path, "w") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        if origin_path is not None and "id" in word_data:
            _remove_key_from_file(origin_path, str(word_data["id"]))


def _contributor_from_origin(origin_path: Path | None, prefix: str) -> str:
    if origin_path is None:
        return "primary"
    stem = origin_path.stem
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return stem


def _remove_key_from_file(path: Path, key: str) -> None:
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    if key in data:
        del data[key]
    with open(path, "w") as f:
        if data:
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            f.write("{}")

# -*- coding: utf-8 -*-

import json
from pathlib import Path

from tools.printer import printer as pr

AdditionsDict = dict[str, dict[str, str | int]]


class AdditionsManager:
    from db.models import DpdHeadword
    from gui2.toolkit import ToolKit

    def __init__(self, toolkit: ToolKit):
        self.paths = toolkit.paths
        self.additions_path = self.paths.additions_path
        self._origin: dict[str, Path] = {}
        self.additions_dict: AdditionsDict = self.load_additions()

    def load_additions(self) -> AdditionsDict:
        """Primary user: non-destructively merge all contributor files.
        Contributor (non-primary) user: load only their own file.
        """
        merged: AdditionsDict = {}
        self._origin = {}

        if self.additions_path.name == "additions.json":
            # Primary user: read every additions_*.json (excluding _added).
            data_dir = self.additions_path.parent
            for contrib_file in sorted(data_dir.glob("additions_*.json")):
                if "additions_added" in contrib_file.name:
                    continue
                try:
                    with open(contrib_file, encoding="utf-8") as f:
                        contrib_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
                for key, value in contrib_data.items():
                    if key in merged:
                        pr.red(
                            f"duplicate addition key {key} in {contrib_file.name}; "
                            f"overriding previous origin {self._origin[key].name}"
                        )
                    merged[key] = value
                    self._origin[key] = contrib_file
        else:
            # Contributor user: read their own file only.
            try:
                with open(self.additions_path, encoding="utf-8") as f:
                    merged = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

        return merged

    def _save_dict(self, data: AdditionsDict) -> None:
        with open(self.additions_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def save_additions(self) -> None:
        self._save_dict(self.additions_dict)

    def add_additions(self, word: DpdHeadword, comment: str) -> None:
        word_dict = {k: v for k, v in vars(word).items() if not k.startswith("_")}
        word_dict["comment"] = comment
        # Key = "{username}_{id}": unique across contributors (username) and
        # stable per word (id + dedup), so re-saving the same word overwrites
        # its one live entry (latest wins) instead of piling up duplicates the
        # reviewer would process repeatedly. Reuse an existing entry's key even
        # if it predates this scheme (e.g. an old uuid key).
        key = self._key_for_id(word.id) or f"{self._username()}_{word.id}"
        self.additions_dict[key] = word_dict
        self.save_additions()

    def _username(self) -> str:
        """The contributor this file belongs to, from its name
        (additions_{username}.json). Primary user's additions.json → '1'."""
        stem = self.additions_path.stem
        prefix = "additions_"
        return stem[len(prefix) :] if stem.startswith(prefix) else "1"

    def _key_for_id(self, id_no: int) -> str | None:
        """Return the existing key for an entry with this db id, or None."""
        for key, entry in self.additions_dict.items():
            if entry.get("id") == id_no:
                return key
        return None

    def is_not_in_additions(self, id_no: int) -> bool:
        return self._key_for_id(id_no) is None

    def get_next_addition(
        self,
    ) -> tuple[dict[str, str | int] | None, Path | None, str | None, int]:
        """Retrieves and removes the next addition from the in-memory queue.

        Returns (addition, origin_path, source_key, additions_remaining).
        source_key is the key as it appears in the contributor file — needed
        because the DB may assign a different id when the addition is committed.
        All three are None/0 if no additions are available.
        """
        if not self.additions_dict:
            return None, None, None, 0

        first_key = next(iter(self.additions_dict))
        addition = self.additions_dict.pop(first_key)
        origin = self._origin.pop(first_key, None)
        return addition, origin, first_key, len(self.additions_dict)

    def save_processed_addition(
        self,
        word_data: dict[str, str],
        origin_path: Path | None = None,
        source_key: str | None = None,
    ) -> None:
        """Append processed addition to additions_added.json, tagging the
        contributor, and remove that key from the origin contributor file.
        source_key is the key as stored in the contributor file (may differ
        from word_data["id"] which gets a new DB-assigned value on commit).
        """
        contributor = _contributor_from_origin(origin_path, prefix="additions_")

        existing_data: list[dict] = []
        try:
            with open(self.paths.additions_added_path, encoding="utf-8") as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        tagged = {**word_data, "_contributor": contributor}
        existing_data.append(tagged)

        with open(self.paths.additions_added_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        if origin_path is not None and source_key is not None:
            _remove_key_from_file(origin_path, source_key)


def _contributor_from_origin(origin_path: Path | None, prefix: str) -> str:
    if origin_path is None:
        return "primary"
    stem = origin_path.stem
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return stem


def _remove_key_from_file(path: Path, key: str) -> None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    if key in data:
        del data[key]
    with open(path, "w", encoding="utf-8") as f:
        if data:
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            f.write("{}")
